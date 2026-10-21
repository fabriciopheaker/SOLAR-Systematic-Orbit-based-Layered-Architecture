import ast
from pathlib import Path

from nucleus.rules.scanner.secret_guards import (
    SUPPRESSION_MARKER,
    is_default,
    is_suppressed,
)
from nucleus.rules.scanner.secret_literal import SecretLiteral
from nucleus.rules.scanner.secret_names import is_secret_name
from nucleus.rules.scanner.secret_patterns import PLACEHOLDER_PREFIX
from nucleus.rules.scanner.source_files import source_files


class SecretScanner:
    """
    Scanner responsável por identificar SEGREDOS HARDCODED no
    código-fonte.

    Encontra valores LITERAIS atribuídos a nomes sensíveis:

        SECRET_KEY = "abc123"
        DATABASE_PASSWORD = "root"
        CONFIG = {"token": "..."}          (não: não é atribuição direta)
        connect(password="root")           (keyword argument)

    NÃO encontra:

        SECRET_KEY = os.environ["SECRET_KEY"]    (vem do ambiente)
        password = ""                            (valor vazio)
        password_field = "senha"                 (nome não é sensível)

    O scanner NÃO decide se há violação: isso é responsabilidade
    da Rule SOLAR-SEG-001.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    def __init__(
        self,
        root: Path,
        suppression_marker: str = SUPPRESSION_MARKER,
        default_prefix: str = PLACEHOLDER_PREFIX
    ):
        # `resolve()`: cada achado guarda o caminho RELATIVO à
        # raiz, e a subtração só funciona se os dois vierem do
        # mesmo ponto de partida.
        self.root = root.resolve()

        # Injetáveis para o teste poder usar marcador e prefixo
        # próprios, sem depender das constantes do projeto.
        self.suppression_marker = suppression_marker
        self.default_prefix = default_prefix

    def scan(self) -> list[SecretLiteral]:
        """
        Percorre o projeto e retorna os literais sensíveis.
        """

        findings: list[SecretLiteral] = []

        # O laço de arquivos fica aqui e não em `_scan_file`: a
        # lista de fontes varridas é a mesma para todos os
        # scanners de código, e essa regra mora em `source_files`.
        for file in source_files(self.root):

            findings.extend(
                self._scan_file(file)
            )

        return findings

    def _scan_file(self, file: Path) -> list[SecretLiteral]:
        """
        Analisa um único arquivo Python.
        """

        # Lê o TEXTO; nunca importa o módulo. Analisar código de
        # terceiros executando-o seria o oposto de segurança.
        source = file.read_text(encoding="utf-8")

        tree = ast.parse(
            source,
            filename=str(file)
        )

        # O local vai RELATIVO e com barra normal: o relatório
        # precisa sair igual rodando no Windows ou no contêiner.
        relative = file.relative_to(self.root).as_posix()

        # O fonte em linhas, ao lado da árvore: o marcador de
        # exceção é um COMENTÁRIO, e comentário não existe na AST —
        # a única forma de enxergá-lo é pelo texto.
        lines = source.splitlines()

        findings: list[SecretLiteral] = []

        # `ast.walk` desce na árvore inteira: o segredo pode estar
        # dentro de uma função, de uma classe ou de um `if`, não só
        # no topo do módulo.
        for node in ast.walk(tree):

            # As três formas de ligar um nome sensível a um literal
            # que aparecem na prática: atribuição, atribuição com
            # anotação e argumento nomeado.
            if isinstance(node, ast.Assign):
                findings.extend(
                    self._assignment(node, relative, lines)
                )

            elif isinstance(node, ast.AnnAssign):
                findings.extend(
                    self._annotated_assignment(node, relative, lines)
                )

            elif isinstance(node, ast.keyword):
                findings.extend(
                    self._keyword(node, relative, lines)
                )

        return findings

    def _assignment(
        self,
        node: ast.Assign,
        file: str,
        lines: list[str]
    ) -> list[SecretLiteral]:
        """
        SECRET_KEY = "abc123"
        """

        value = self._literal(node.value)

        if value is None:
            return []

        return [
            self._finding(
                name=target.id,
                value=value,
                file=file,
                line=node.lineno,
                literal=node.value,
                lines=lines
            )
            for target in node.targets
            if isinstance(target, ast.Name)
            and is_secret_name(target.id)
        ]

    def _annotated_assignment(
        self,
        node: ast.AnnAssign,
        file: str,
        lines: list[str]
    ) -> list[SecretLiteral]:
        """
        SECRET_KEY: str = "abc123"
        """

        value = self._literal(node.value)

        # Alvo que não é nome simples (ex.: `self.key: str = "x"`)
        # fica de fora: atributo de instância não é nome global, e
        # marcá-lo aqui daria falso positivo em DTO.
        if value is None or not isinstance(node.target, ast.Name):
            return []

        if not is_secret_name(node.target.id):
            return []

        return [
            self._finding(
                name=node.target.id,
                value=value,
                file=file,
                line=node.lineno,
                literal=node.value,
                lines=lines
            )
        ]

    def _keyword(
        self,
        node: ast.keyword,
        file: str,
        lines: list[str]
    ) -> list[SecretLiteral]:
        """
        connect(password="root")
        """

        # `node.arg is None` é o `**kwargs` solto: sem nome, não há
        # o que comparar com a lista de nomes sensíveis.
        if node.arg is None or not is_secret_name(node.arg):
            return []

        value = self._literal(node.value)

        if value is None:
            return []

        return [
            self._finding(
                name=node.arg,
                value=value,
                file=file,
                line=node.lineno,
                literal=node.value,
                lines=lines
            )
        ]

    def _finding(
        self,
        name: str,
        value: str,
        file: str,
        line: int,
        literal: ast.AST,
        lines: list[str]
    ) -> SecretLiteral:
        """
        Monta o achado, marcando os casos que exigem contexto.

        O scanner descreve; a Rule SOLAR-SEG-001 decide a
        política:

            suppressed   o trecho está anotado com o marcador de
                         exceção (`# solar:allow-secret`);
            default      o valor começa com o prefixo de DEFAULT
                         (espera vir do ambiente).
        """

        return SecretLiteral(
            name=name,
            value=value,
            file=file,
            line=line,
            suppressed=is_suppressed(
                literal,
                lines,
                self.suppression_marker
            ),
            default=is_default(value, self.default_prefix)
        )

    def _literal(self, node: ast.AST | None) -> str | None:
        """
        Retorna o valor de um literal de texto NÃO VAZIO.

        Qualquer outra expressão (variável, chamada, f-string)
        não é um segredo hardcoded.
        """

        # Três descartes, do mais comum ao mais raro: não é
        # literal (variável, chamada, f-string), é literal mas não
        # de texto (número, None, True) ou é texto vazio.
        if not isinstance(node, ast.Constant):
            return None

        if not isinstance(node.value, str):
            return None

        # `strip()`: `""` e `"   "` são o mesmo "sem valor". Um
        # espaço em branco é o que se escreve quando o valor ainda
        # não se sabe — não é segredo.
        if not node.value.strip():
            return None

        return node.value
