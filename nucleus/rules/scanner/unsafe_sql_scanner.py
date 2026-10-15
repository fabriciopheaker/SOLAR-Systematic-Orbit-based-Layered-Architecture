# Scanner de SQL construído por INTERPOLAÇÃO.
#
# Só produz achado quando um PEDAÇO DE SQL encontra um VALOR DINÂMICO.
# Concatenar dois literais (`"SELECT ..." + " WHERE ..."`) é estático e
# não vira achado — daí a checagem em duas partes: um lado é SQL e o
# outro NÃO é literal.
#
# Três formas são reconhecidas, porque são as três que aparecem na
# prática: f-string, concatenação/`%` e `.format()`.
#
# O código NÃO é executado: a análise é sobre a AST.
import ast
from pathlib import Path

from nucleus.rules.scanner.source_files import source_files
from nucleus.rules.scanner.unsafe_sql import UnsafeSql


class UnsafeSqlScanner:
    """
    Scanner responsável por identificar CONSTRUÇÕES INSEGURAS de
    SQL no código-fonte.

    Uma construção é insegura quando um trecho SQL é INTERPOLADO
    com valor dinâmico:

        "SELECT * FROM users WHERE id = " + user_id      (concatenation)
        f"SELECT * FROM users WHERE id = {user_id}"      (f-string)
        "SELECT * FROM users WHERE id = %s" % user_id    (percent)
        "SELECT * FROM users WHERE id = {}".format(uid)  (format)

    É seguro quando o SQL é estático:

        "SELECT * FROM users WHERE id = :id"
        cursor.execute(sql, {"id": user_id})

    O scanner NÃO decide se há violação: isso é responsabilidade
    da Rule SOLAR-ARCH-024.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    # Palavras que identificam um trecho como SQL.
    #
    # Em MINÚSCULAS porque a comparação é feita sobre o texto
    # rebaixado — `select` e `SELECT` são a mesma coisa.
    #
    # A maioria termina com ESPAÇO, e isso é proposital: separa `where`
    # (a cláusula) de `somewhere` (a palavra). `order by` e `group by`
    # são as duas exceções, porque já são expressões de duas palavras.
    SQL_KEYWORDS = (
        "select ",
        "insert ",
        "update ",
        "delete ",
        "where ",
        " from ",
        " join ",
        "values ",
        "order by",
        "group by",
    )

    def __init__(self, root: Path):
        # `resolve()`: `_module_name` subtrai a raiz do caminho de cada
        # arquivo, e a subtração só funciona com os dois vindo do
        # mesmo ponto de partida.
        self.root = root.resolve()

    def scan(self) -> list[UnsafeSql]:
        """
        Percorre o projeto e retorna as construções inseguras.
        """

        findings: list[UnsafeSql] = []

        for file in source_files(self.root):

            findings.extend(
                self._scan_file(file)
            )

        return findings

    def _scan_file(self, file: Path) -> list[UnsafeSql]:
        """
        Analisa um único arquivo Python.
        """

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        file_path = file.relative_to(self.root).as_posix()
        module = self._module_name(file)

        findings: list[UnsafeSql] = []

        # Deduplicaçao por (forma, linha): uma construção aninhada em
        # outra — `f"..." + f"..."` — é visitada duas vezes pelo
        # `ast.walk`, e o mesmo achado não pode sair repetido no
        # relatório.
        seen: set[tuple[str, int]] = set()

        for node in ast.walk(tree):

            kind = self._kind(node)

            if kind is None:
                continue

            # A FORMA entra na chave: na mesma linha, uma f-string e
            # uma concatenação são dois problemas diferentes.
            key = (kind, node.lineno)

            if key in seen:
                continue

            seen.add(key)

            findings.append(
                UnsafeSql(
                    module=module,
                    kind=kind,
                    file=file_path,
                    line=node.lineno
                )
            )

        return findings

    def _kind(self, node: ast.AST) -> str | None:
        """
        Classifica a construção insegura, quando houver.
        """

        # Três formas, uma por tipo de nó: f-string é `JoinedStr`,
        # `+`/`%` são `BinOp` e `.format()` é `Call`. Nó de outro tipo
        # devolve `None` e o laço segue.
        if isinstance(node, ast.JoinedStr):
            return self._fstring(node)

        if isinstance(node, ast.BinOp):
            return self._binary(node)

        if isinstance(node, ast.Call):
            return self._format_call(node)

        return None

    def _fstring(self, node: ast.JoinedStr) -> str | None:
        """
        f"SELECT ... {valor}"
        """

        # `values` traz as partes da f-string: os pedaços de texto são
        # `Constant` e as interpolações são `FormattedValue`. Basta UM
        # pedaço de texto ser SQL — a interpolação em si é garantida
        # pelo próprio tipo do nó.
        for value in node.values:

            if self._is_sql_literal(value):
                return "f-string"

        return None

    def _binary(self, node: ast.BinOp) -> str | None:
        """
        "SELECT ... " + valor
        "SELECT ... %s" % valor
        """

        # Só duas operações interessam: `+` (concatenação) e `%`
        # (formatação antiga). `/`, `*` e afins devolvem `None`.
        if isinstance(node.op, ast.Add):
            kind = "concatenation"
        elif isinstance(node.op, ast.Mod):
            kind = "percent"
        else:
            return None

        # Os DOIS lados são testados, em ambas as ordens: `sql + x` e
        # `x + sql` são o mesmo problema escrito de duas formas.
        #
        # A condição é "um lado é SQL E o outro NÃO é literal". Com os
        # dois literais o resultado é estático — concatenar pedaços de
        # SQL não é injeção.
        if self._is_sql_literal(node.right) and not self._is_static(
            node.left
        ):
            return kind

        if self._is_sql_literal(node.left) and not self._is_static(
            node.right
        ):
            return kind

        return None

    def _format_call(self, node: ast.Call) -> str | None:
        """
        "SELECT ... {}".format(valor)
        """

        func = node.func

        # Precisa ser um ATRIBUTO (`.format`), e não uma chamada solta.
        if not isinstance(func, ast.Attribute):
            return None

        if func.attr != "format":
            return None

        # E o ALVO do `.format()` tem que ser o SQL — `x.format()`
        # sobre outra coisa não interessa.
        if self._is_sql_literal(func.value):
            return "format"

        return None

    def _is_sql_literal(self, node: ast.AST) -> bool:
        """
        Um literal de texto que contém SQL.
        """

        # Precisa ser literal de TEXTO: um nome de variável pode se
        # chamar `sql` e não ser SQL nenhum.
        if not isinstance(node, ast.Constant):
            return False

        if not isinstance(node.value, str):
            return False

        # `lower()` uma vez, fora do `any`: dentro, o mesmo texto seria
        # rebaixado a cada palavra comparada.
        text = node.value.lower()

        return any(keyword in text for keyword in self.SQL_KEYWORDS)

    def _is_static(self, node: ast.AST) -> bool:
        """
        Indica se a expressão é um literal estático (não interpolado).
        """

        # Constante = valor fixo no código. Nome de variável, chamada
        # e f-string são dinâmicos — e é o dinâmico que caracteriza a
        # interpolação.
        return isinstance(node, ast.Constant)

    def _module_name(self, file: Path) -> str:
        """
        Converte o caminho do arquivo em nome de módulo.

        orbits/database/persistence/persistence.py
            → orbits.database.persistence.persistence
        """

        relative = file.relative_to(self.root)

        # `with_suffix("")` tira o `.py` e as partes viram o caminho
        # pontuado. Não há import envolvido — é conversão de formato, e
        # por isso vale para qualquer layout do projeto.
        return ".".join(
            relative.with_suffix("").parts
        )
