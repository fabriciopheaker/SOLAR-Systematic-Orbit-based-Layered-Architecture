import ast
from pathlib import Path

from nucleus.rules.scanner.outbound_request import OutboundRequest
from nucleus.rules.scanner.source_files import source_files


class OutboundRequestScanner:
    """
    Scanner responsável por identificar chamadas para serviços
    EXTERNOS e descrever como a URL é montada.

    SSRF (Server-Side Request Forgery) acontece quando a aplicação
    busca uma URL que QUEM CHAMOU escolheu:

        requests.get(request.args["url"])           ❌
        httpx.get(f"http://{host}/health")          ❌
        requests.get(url)                           ❌

    A mesma chamada, com a URL vinda de constante ou de
    configuração, é legítima:

        requests.get("https://api.exemplo.com/users")   ✅
        requests.get(f"{BASE_URL}/users")               ✅
        requests.get(environment.get("API_URL"))        ✅

    O scanner NÃO tenta decidir isso: ele descreve QUAIS
    identificadores compõem a URL, e a Rule SOLAR-SEG-010 aplica
    a política.

    Além da URL, o scanner reconhece o cliente HTTP
    (`requests`, `httpx`, `aiohttp`, `urllib`).

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    # Bibliotecas de comunicação externa.
    EXTERNAL_PACKAGES = (
        "aiohttp",
        "httpx",
        "requests",
        "urllib",
    )

    # Funções que buscam uma URL sem serem métodos de um cliente.
    URL_FUNCTIONS = frozenset({
        "urlopen",
        "urlretrieve",
    })

    # Métodos HTTP das bibliotecas de comunicação externa.
    #
    # Exigir o MÉTODO (e não só o pacote) evita confundir uma
    # variável com o nome da biblioteca:
    #
    #     requests.extend(...)   ← uma LISTA chamada "requests"
    #     requests.get(...)      ← a biblioteca
    HTTP_METHODS = frozenset({
        "delete",
        "get",
        "head",
        "options",
        "patch",
        "post",
        "put",
        "request",
        "stream",
    })

    URL_KEYWORD = "url"

    # `self`/`cls` não são origem de dado: o que importa é o
    # ATRIBUTO acessado (ex.: `self.base_url` conta como
    # "base_url").
    SELF_NAMES = frozenset({"cls", "self"})

    def __init__(self, root: Path):
        self.root = root.resolve()

    def scan(self) -> list[OutboundRequest]:
        """
        Percorre o projeto e retorna as chamadas encontradas.
        """

        requests: list[OutboundRequest] = []

        for file in source_files(self.root):

            requests.extend(
                self._scan_file(file)
            )

        return requests

    def _scan_file(self, file: Path) -> list[OutboundRequest]:
        """
        Analisa um único arquivo Python.
        """

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        relative = file.relative_to(self.root).as_posix()

        requests: list[OutboundRequest] = []

        for node in ast.walk(tree):

            if not isinstance(node, ast.Call):
                continue

            url = self._url_argument(node)

            if url is None:
                continue

            requests.append(
                OutboundRequest(
                    package=self._package(node),
                    url=ast.unparse(url),
                    names=self._names(url),
                    file=relative,
                    line=node.lineno
                )
            )

        return requests

    def _url_argument(self, node: ast.Call) -> ast.AST | None:
        """
        Devolve a expressão da URL, quando existir.

        A ausência de URL significa que a chamada não é um pedido
        a serviço externo (ex.: `requests.Session()`).

        Limitação conhecida: a chamada precisa ser feita PELA
        biblioteca (`requests.get(...)`). Um cliente já construído
        (`session.get(url)`) não é reconhecido, porque o nome não
        diz de onde ele veio.
        """

        if not self._is_external(self._name(node.func)):
            return None

        for keyword in node.keywords:

            if keyword.arg == self.URL_KEYWORD:
                return keyword.value

        if node.args:
            return node.args[0]

        return None

    def _package(self, node: ast.Call) -> str:
        """
        Biblioteca usada na chamada.
        """

        return self._name(node.func).split(".")[0]

    def _is_external(self, name: str) -> bool:
        """
        Indica se a chamada é de comunicação externa.

        A biblioteca tem que ser a RAIZ do nome e o ÚLTIMO segmento
        tem que ser um método de busca — as duas coisas juntas.
        Assim um dado local com nome igual ao da biblioteca não
        vira comunicação externa.
        """

        segments = name.split(".")

        if segments[0] not in self.EXTERNAL_PACKAGES:
            return False

        leaf = segments[-1]

        if leaf in self.URL_FUNCTIONS:
            return True

        return leaf in self.HTTP_METHODS

    def _names(self, node: ast.AST) -> frozenset[str]:
        """
        Identificadores que compõem a expressão da URL.
        """

        names: set[str] = set()

        for child in ast.walk(node):

            if isinstance(child, ast.Name):

                if child.id not in self.SELF_NAMES:
                    names.add(child.id)

            elif (
                isinstance(child, ast.Attribute)
                and isinstance(child.value, ast.Name)
                and child.value.id in self.SELF_NAMES
            ):
                names.add(child.attr)

        return frozenset(names)

    def _name(self, node: ast.AST) -> str:
        """
        Converte o alvo de uma chamada em nome pontuado.
        """

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):

            base = self._name(node.value)

            return f"{base}.{node.attr}" if base else node.attr

        return ""
