# SOLAR-SEG-005 — o Controller não grava arquivo.
#
# Quem grava é a fachada `Storage`, que já bloqueia nome que escapa
# da raiz e concentra a política de armazenamento. Um Controller que
# chama `open` ou `shutil.copy` passou a ter as duas
# responsabilidades — gravar e orquestrar.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import SECURITY, Rule, rule_code
from nucleus.rules.scanner.upload_handling import UploadHandling


class UploadsMustUseStorage(Rule):
    """
    Regra arquitetural:

    SOLAR-SEG-005

    Upload seguro: o arquivo recebido NÃO pode ser manipulado
    diretamente pelo Controller. Ele deve ser entregue à abstração
    de armazenamento da arquitetura (Storage).

    É VIOLAÇÃO:

        class DocumentController:

            def upload(self, arquivo):
                arquivo.save("/tmp/documento.pdf")        ❌
                open("documento.pdf", "wb")               ❌
                mimetypes.guess_type(arquivo.filename)    ❌
                shutil.copy(arquivo, destino)             ❌

    Correto:

        class DocumentController:

            def upload(self, arquivo):
                UploadDocumentUseCase.execute(
                    UploadDocumentInput(arquivo=arquivo)
                )                                         ✅

    O UseCase usa a fachada de armazenamento:

        Storage.save("documents/contrato.pdf", conteudo)

    Quem GRAVA o arquivo é a fachada Storage (LocalStorageDriver
    ou um driver de nuvem), que já protege contra nomes que
    escapam da raiz do storage.

    A validação estrutural da entrada (arquivo enviado, tamanho,
    extensão, MIME type) é responsabilidade do Validator da
    SOLAR-ROF-001 — não desta regra.

    O contexto desta regra é um UploadHandling.
    """

    # Primitivos de arquivo proibidos no Controller.
    #
    # A lista mistura FUNÇÕES (`open`, `copy`, `copy2`, `move`) e
    # MÓDULOS (`shutil`, `tempfile`, `mimetypes`, `aiofiles`) de
    # propósito: o scanner registra os dois, e `shutil.copy(...)` é
    # o mesmo problema que `copy(...)` — escrito de outra forma.
    FORBIDDEN_PRIMITIVES = frozenset({
        "open",
        "write_bytes",
        "write_text",
        "copy",
        "copy2",
        "copyfile",
        "move",
        "mkdtemp",
        "NamedTemporaryFile",
        "shutil",
        "tempfile",
        "mimetypes",
        "aiofiles",
    })

    def code(self) -> str:
        return rule_code(SECURITY, 5)

    def description(self) -> str:
        return (
            "Upload deve passar pela abstração de armazenamento "
            "(Storage); o Controller não manipula arquivo."
        )

    def validate(self, handling: UploadHandling) -> None:

        # Interseção: dos primitivos que o Controller usa, quais estão
        # na lista proibida. Vazio = o Controller não toca em arquivo,
        # que é o caso correto. `sorted` só para a mensagem não variar
        # entre execuções.
        offending = sorted(
            handling.primitives & self.FORBIDDEN_PRIMITIVES
        )

        if not offending:
            return

        raise SolarException(
            self._build_message(handling, offending)
        )

    def _build_message(
        self,
        handling: UploadHandling,
        offending: list[str]
    ) -> str:

        return (
            f"{self.code()}: "
            f"o Controller '{handling.controller}' "
            f"({handling.file}:{handling.line}) manipula arquivo "
            f"diretamente usando {', '.join(offending)}. "
            f"O arquivo deve ser entregue ao UseCase e gravado pela "
            f"abstração Storage (nucleus.storage.Storage), que "
            f"aplica as proteções de armazenamento."
        )
