# Scanner de segredo por CONTEÚDO — o par do SecretScanner, que
# casa por NOME.
#
# Os dois caminham pela mesma AST, mas com perguntas diferentes:
# aqui a pergunta é "este TEXTO parece uma credencial?", e a
# resposta vem dos padrões de `secret_patterns`.
#
# Este scanner produz `SecretOccurrence` — descrição, não
# julgamento. A política é da SOLAR-SEG-004.
import ast
from collections.abc import Iterable
from pathlib import Path

from nucleus.rules.scanner.secret_guards import (
    SUPPRESSION_MARKER,
    is_suppressed,
)
from nucleus.rules.scanner.secret_occurrence import SecretOccurrence
from nucleus.rules.scanner.secret_patterns import is_example, match_secret
from nucleus.rules.scanner.source_files import (
    resolve_exclusions,
    source_files,
)


class SecretContentScanner:
    """
    Scanner responsável por identificar SEGREDOS no código-fonte
    pelo CONTEÚDO, independentemente do nome da variável.

    Encontra:

        CHAVE = "AKIAIOSFODNN7EXAMPLE"          (aws-access-key)
        HEADER = "-----BEGIN RSA PRIVATE KEY-----"
        ENCODED = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc"

    NÃO encontra:

        CHAVE = os.environ["AWS_ACCESS_KEY_ID"]

    Complementa a SOLAR-SEG-001 (que casa pelo NOME).

    Um casamento de padrão NÃO é automaticamente uma violação. O
    scanner apenas DESCREVE o que achou, marcando os casos que
    exigem contexto — a política fica na Rule SOLAR-SEG-004:

        documentation   o literal é docstring/texto solto,
                        não um valor usado pelo programa;
        suppressed      o trecho está anotado com
                        SUPPRESSION_MARKER;
        example         o valor é um exemplo/placeholder
                        conhecido (ver secret_patterns).

    Para não varrer o mundo, diretórios sem código de produção
    (testes, fixtures, exemplos, caches) ficam de fora — ver
    nucleus.rules.scanner.source_files.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    def __init__(
        self,
        root: Path,
        excluded_directories: Iterable[str] | None = None,
        suppression_marker: str = SUPPRESSION_MARKER
    ):
        self.root = root.resolve()

        # `resolve_exclusions` completa a lista recebida com os
        # diretórios que nunca contam como produção (testes,
        # fixtures, caches). Quem varre informa só o que é
        # específico do seu caso.
        self.excluded_directories = resolve_exclusions(
            excluded_directories
        )

        # Injetável pelo mesmo motivo do SecretScanner: o teste usa
        # o marcador que quiser.
        self.suppression_marker = suppression_marker

    def scan(self) -> list[SecretOccurrence]:
        """
        Percorre o projeto e retorna as ocorrências encontradas.
        """

        occurrences: list[SecretOccurrence] = []

        for file in source_files(
            self.root,
            self.excluded_directories
        ):

            occurrences.extend(
                self._scan_file(file)
            )

        return occurrences

    def _scan_file(self, file: Path) -> list[SecretOccurrence]:
        """
        Analisa um único arquivo Python.

        Docstrings e blocos de texto SÃO analisados (na AST eles
        são literais como qualquer outro), mas marcados como
        documentação — quem decide ignorar é a Rule.

        Comentários com "#" não existem na AST e não são vistos.
        """

        source = file.read_text(encoding="utf-8")

        tree = ast.parse(
            source,
            filename=str(file)
        )

        relative = file.relative_to(self.root).as_posix()

        lines = source.splitlines()

        # O mapa de pais é montado UMA vez por arquivo: saber se o
        # literal é docstring exige olhar para o nó de cima, e
        # procurá-lo a cada literal seria varrer a árvore N vezes.
        parents = _parent_map(tree)

        occurrences: list[SecretOccurrence] = []

        # Quatro filtros em sequência, do mais barato ao mais caro:
        # só literal, só de texto, só o que casa com algum padrão.
        # Ao contrário do SecretScanner, aqui NÃO se olha o nome da
        # variável — só o conteúdo.
        for node in ast.walk(tree):

            if not isinstance(node, ast.Constant):
                continue

            if not isinstance(node.value, str):
                continue

            pattern = match_secret(node.value)

            if pattern is None:
                continue

            occurrences.append(
                SecretOccurrence(
                    pattern=pattern,
                    file=relative,
                    line=node.lineno,
                    documentation=_is_documentation(node, parents),
                    suppressed=is_suppressed(
                        node,
                        lines,
                        self.suppression_marker
                    ),
                    example=is_example(node.value)
                )
            )

        return occurrences

def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    """
    Mapeia cada nó da AST para o seu pai.
    """

    parents: dict[ast.AST, ast.AST] = {}

    # Percorre os PAIS para poder gravar a volta (`filho -> pai`):
    # `iter_child_nodes` dá os filhos de cada nó, e é isso que
    # permite registrar quem é o pai de quem.
    for parent in ast.walk(tree):

        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    return parents


def _is_documentation(
    node: ast.Constant,
    parents: dict[ast.AST, ast.AST]
) -> bool:
    """
    Indica se o literal é um bloco de DOCUMENTAÇÃO.

    Um literal que é a PRÓPRIA instrução (ast.Expr) é docstring ou
    texto solto: não está atribuído a nada, logo o programa não o
    usa como valor. Um literal atribuído tem como pai Assign,
    AnnAssign, Dict, Call, ... e é um valor de verdade.
    """

    parent = parents.get(node)

    # `parent.value is node` e não `==`: a IDENTIDADE garante que
    # este literal é a instrução inteira. Um literal dentro de uma
    # expressão maior (tupla, dict, chamada) é valor de verdade —
    # mesmo que o texto pareça um segredo — e não deve ser tratado
    # como documentação.
    return isinstance(parent, ast.Expr) and parent.value is node
