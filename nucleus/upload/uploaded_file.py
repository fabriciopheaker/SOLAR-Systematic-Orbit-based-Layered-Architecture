from dataclasses import dataclass


@dataclass(frozen=True)
class UploadedFile:
    """
    Representa um ARQUIVO RECEBIDO por upload.

    name:
        Nome ORIGINAL enviado pelo cliente. NUNCA deve ser usado
        para gravar — o FileSanitizer normaliza e o Storage
        protege a raiz.

    content_type:
        MIME type informado no multipart.

    content:
        Conteúdo do arquivo.

    O UploadedFile é o CONTRATO DE ENTRADA do upload: a partir
    dele o FileSanitizer normaliza e o FileValidator valida.
    """

    name: str
    content_type: str
    content: bytes

    @property
    def size(self) -> int:
        """
        Tamanho do arquivo em bytes.
        """

        return len(self.content)

    @property
    def extension(self) -> str:
        """
        Extensão informada, em minúsculas (ex.: ".pdf").

        Retorna "" quando o nome não tem extensão.
        """

        if "." not in self.name:
            return ""

        # O ÚLTIMO ponto, e não o primeiro: em "contrato.v2.pdf" a
        # extensão é ".pdf". Em minúsculas porque ".PDF" e ".pdf"
        # são a mesma coisa para quem compara com a política — e
        # deixar a diferença de caixa seria um jeito de burlar a
        # lista de extensões permitidas.
        return "." + self.name.rsplit(".", 1)[-1].lower()
