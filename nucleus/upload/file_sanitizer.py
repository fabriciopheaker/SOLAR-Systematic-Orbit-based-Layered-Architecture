import re
from dataclasses import replace
from pathlib import PurePosixPath

from nucleus.contracts.sanitizer import Sanitizer
from nucleus.upload.uploaded_file import UploadedFile


class FileSanitizer(Sanitizer):
    """
    Sanitizer de UPLOAD.

    Normaliza o NOME dos arquivos recebidos antes de qualquer
    validação:

        "../../etc/passwd"       → "passwd"
        "..\\\\..\\\\windows\\\\x.pdf"   → "x.pdf"
        "relatório<>.pdf"        → "relatório.pdf"
        ""                       → "arquivo"

    O nome enviado pelo cliente NUNCA é confiável. Mesmo que o
    Storage já proteja a raiz, o nome saneado é o que circula na
    aplicação.

    Implementa o contrato Sanitizer da SOLAR-ARCH-013.
    """

    # Nome usado quando nada sobra do original.
    FALLBACK_NAME = "arquivo"

    # Limite de tamanho do nome (padrão dos sistemas de arquivos).
    MAX_NAME_LENGTH = 255

    # Caracteres que confundem caminhos e sistemas.
    # Os caracteres que confundem caminho e sistema.
    #
    #   /  \\         separadores de caminho — tentativa de sair da
    #                  pasta ou de escrever em outro diretório;
    #   \x00-\x1f     caracteres de controle, que truncam nome de
    #                  arquivo em algumas camadas;
    #   : * ? " < > |  o Windows recusa um arquivo com estes no
    #                  nome — barrar aqui evita quebrar lá.
    FORBIDDEN_CHARACTERS = re.compile(r"[\x00-\x1f\x7f/\\:*?\"<>|]")

    def sanitize(self, payload) -> list[UploadedFile]:
        """
        Recebe os arquivos do upload e devolve a lista com os
        nomes sanitizados.

        Aceita tanto a lista de arquivos quanto um mapa com a
        chave "files".
        """

        # `replace` porque UploadedFile é imutável: o sanitizado é
        # um objeto NOVO, e o original continua como chegou, para
        # quem precisar dele (um log de auditoria, por exemplo).
        return [
            replace(file, name=safe_filename(file.name))
            for file in upload_files(payload)
        ]


def upload_files(payload) -> list[UploadedFile]:
    """
    Extrai a lista de arquivos de um payload de upload.

    Aceita:

        [UploadedFile(...), ...]            → lista direta
        {"files": [UploadedFile(...), ...]} → mapa com "files"
    """

    if isinstance(payload, dict):
        return list(payload.get("files", []))

    if payload is None:
        return []

    return list(payload)


def safe_filename(name: str) -> str:
    """
    Normaliza o nome de um arquivo recebido.

    Remove diretórios, caracteres de controle e caracteres
    proibidos; limita o tamanho; devolve um fallback quando nada
    resta.
    """

    if not name:
        return FileSanitizer.FALLBACK_NAME

    # "..\\a\\b.pdf" e "../a/b.pdf" chegam sempre com "/".
    normalized = str(name).replace("\\", "/")

    base = PurePosixPath(normalized).name

    base = FileSanitizer.FORBIDDEN_CHARACTERS.sub("", base).strip()

    # "." e ".." não são nomes de arquivo válidos.
    if base in ("", ".", ".."):
        return FileSanitizer.FALLBACK_NAME

    return base[: FileSanitizer.MAX_NAME_LENGTH]
