# Política de upload: o que a aplicação ACEITA receber.
#
# É DADO, e não código dentro do `FileValidator` — assim o mesmo
# validador serve a contratos diferentes, e mudar o que se aceita é
# editar a configuração de um contrato, sem tocar em lógica de
# validação.
from dataclasses import dataclass


@dataclass(frozen=True)
class UploadPolicy:
    """
    Define o que um upload ACEITA.

    allowed_extensions:
        Extensões permitidas, em minúsculas (ex.: {".pdf"}).

    allowed_content_types:
        MIME types permitidos (ex.: {"application/pdf"}).

    max_size_bytes:
        Tamanho máximo de cada arquivo.

    max_files:
        Quantidade máxima de arquivos por entrada.

    verify_content:
        Quando True (padrão), o CONTEÚDO do arquivo é conferido
        contra o tipo declarado pelas assinaturas (magic bytes) —
        é o que impede que um script renomeado para ".pdf" entre
        na aplicação. Tipos sem assinatura conhecida (ex.:
        text/plain) não são verificáveis.

    A policy é definida pela aplicação (não pela SOLAR): cada
    contrato de upload tem as suas. O FileValidator aplica.

    Presets prontos:

        UploadPolicy.documents()
        UploadPolicy.images()
    """

    allowed_extensions: frozenset[str]
    allowed_content_types: frozenset[str]

    # Em BYTES, e não em uma unidade legível: a comparação é feita com o
    # tamanho que a biblioteca informa, sem conversão no caminho.
    max_size_bytes: int

    # Um arquivo por entrada é o padrão mais restritivo; quem aceita
    # vários diz isso explicitamente no seu preset.
    max_files: int = 1

    # LIGADO por padrão: conferir o CONTEÚDO é a defesa contra o arquivo
    # renomeado (o `.pdf` que na verdade é script). Desligar assume o
    # risco — por isso o padrão é o lado seguro.
    verify_content: bool = True

    # `lower()` nas três checagens porque a política guarda tudo em
    # minúsculas: `".PDF"` e `".pdf"` são a mesma extensão, e deixar a
    # diferença de caixa seria um jeito de burlar a lista.

    def allows_extension(self, extension: str) -> bool:
        return extension.lower() in self.allowed_extensions

    def allows_content_type(self, content_type: str) -> bool:
        return content_type.lower() in self.allowed_content_types

    def allows_size(self, size: int) -> bool:
        # `0 < size`: arquivo VAZIO é recusado aqui, e não apenas
        # "pequeno o bastante". Tamanho negativo não existe, mas a
        # comparação também o barraria.
        return 0 < size <= self.max_size_bytes

    # -----------------------------------------------------------------
    # Presets
    # -----------------------------------------------------------------

    @classmethod
    def documents(cls) -> "UploadPolicy":
        """
        Preset para DOCUMENTOS.

        Aceita PDF, Office (moderno e legado) e texto.
        """

        # Extensões e MIME types em listas SEPARADAS porque as duas
        # origens são diferentes: a extensão vem do NOME do arquivo e o
        # MIME vem do cabeçalho — as duas precisam ser conferidas.
        #
        # `10 * 1024 * 1024` escrito como conta, e não como 10485760: o
        # que se quer ler aqui é "10 MB".
        return cls(
            allowed_extensions=frozenset({
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
                ".txt",
            }),
            allowed_content_types=frozenset({
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet",
                "application/vnd.ms-powerpoint",
                "application/vnd.openxmlformats-officedocument."
                "presentationml.presentation",
                "text/plain",
            }),
            max_size_bytes=10 * 1024 * 1024,
            max_files=1,
            verify_content=True
        )

    @classmethod
    def images(cls) -> "UploadPolicy":
        """
        Preset para IMAGENS.

        Aceita PNG, JPEG, GIF e WEBP — todos com assinatura
        verificável.
        """

        # São estes quatro porque os quatro têm assinatura verificável —
        # é o que faz `verify_content=True` valer a pena aqui.
        # `image/jpg` está na lista além de `image/jpeg` porque é o que
        # alguns clientes enviam.
        return cls(
            allowed_extensions=frozenset({
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            }),
            allowed_content_types=frozenset({
                "image/png",
                "image/jpeg",
                "image/jpg",
                "image/gif",
                "image/webp",
            }),
            max_size_bytes=5 * 1024 * 1024,
            max_files=1,
            verify_content=True
        )
