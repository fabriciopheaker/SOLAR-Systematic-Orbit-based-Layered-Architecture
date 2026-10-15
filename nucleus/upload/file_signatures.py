# Assinaturas (magic bytes) dos formatos que a SOLAR reconhece.
#
# Cada entrada é:  (tipo MIME, ALTERNATIVAS)
#
# e cada alternativa é um conjunto de trechos que precisam casar
# JUNTOS, na posição indicada:  (offset, bytes).
#
# Ou seja: a entrada casa quando QUALQUER alternativa casa, e uma
# alternativa casa quando TODOS os seus trechos casam. É o que
# permite expressar tanto o WEBP (RIFF *e* WEBP) quanto o GIF
# (GIF87a *ou* GIF89a).
#
# É esta verificação que pega o caso clássico de ataque:
#
#     script.py  →  renomeado para contrato.pdf
#     content-type declarado: application/pdf
#     (o conteúdo NÃO começa com "%PDF-")
SIGNATURES = (
    (
        "application/pdf",
        (((0, b"%PDF-"),),)
    ),
    (
        "image/png",
        (((0, b"\x89PNG\r\n\x1a\n"),),)
    ),
    (
        "image/jpeg",
        (((0, b"\xff\xd8\xff"),),)
    ),
    (
        "image/gif",
        (
            ((0, b"GIF87a"),),
            ((0, b"GIF89a"),),
        )
    ),
    (
        "image/webp",
        (((0, b"RIFF"), (8, b"WEBP")),)
    ),
    (
        "application/zip",
        (((0, b"PK\x03\x04"),),)
    ),
    (
        "application/x-ole-storage",
        (((0, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),),)
    ),
)

# Tipos declarados que COMPARTILHAM a assinatura de outro tipo.
#
# Formato: tipo declarado → tipo canônico (o que o sniffing
# devolve). Os formatos do Office moderno (.docx/.xlsx/.pptx) são
# contêineres ZIP; o legado (.doc/.xls/.ppt) é OLE.
EQUIVALENTS = {
    "image/jpg": "image/jpeg",
    "application/x-zip-compressed": "application/zip",
    "application/msword": "application/x-ole-storage",
    "application/vnd.ms-excel": "application/x-ole-storage",
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document": "application/zip",
    "application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet": "application/zip",
    "application/vnd.openxmlformats-officedocument."
    "presentationml.presentation": "application/zip",
}

# Quantidade de bytes suficiente para todas as assinaturas.
HEADER_SIZE = 32

_SIGNATURE_MAP = dict(SIGNATURES)


def canonical(content_type: str) -> str:
    """
    Normaliza um tipo declarado para o tipo que o sniffing
    devolve.

        image/jpg        → image/jpeg
        ...wordprocessingml.document → application/zip
    """

    normalized = (content_type or "").strip().lower()

    return EQUIVALENTS.get(normalized, normalized)


def sniff(content: bytes) -> str | None:
    """
    Detecta o tipo REAL do conteúdo pelas assinaturas.

    Devolve o tipo MIME detectado, ou None quando nenhuma
    assinatura conhecida casa (ex.: texto puro).
    """

    header = content[:HEADER_SIZE]

    for mime, alternatives in SIGNATURES:

        if any(
            _matches_requirements(header, requirements)
            for requirements in alternatives
        ):
            return mime

    return None


def is_verifiable(content_type: str) -> bool:
    """
    Indica se o tipo declarado tem assinatura conhecida.

    Tipos sem assinatura (ex.: text/plain) não são verificáveis —
    a checagem de conteúdo não se aplica a eles.
    """

    return canonical(content_type) in _SIGNATURE_MAP


def matches(content: bytes, content_type: str) -> bool:
    """
    Indica se o conteúdo corresponde ao tipo declarado.

    Quando o tipo não tem assinatura conhecida, não há como
    verificar: a resposta é True (a validação de conteúdo não se
    aplica).
    """

    expected = canonical(content_type)

    if expected not in _SIGNATURE_MAP:
        return True

    return sniff(content) == expected


def _matches_requirements(
    header: bytes,
    requirements
) -> bool:
    """
    Verifica se TODOS os trechos de UMA alternativa aparecem nas
    posições exigidas.
    """

    return all(
        header[offset:offset + len(expected)] == expected
        for offset, expected in requirements
    )
