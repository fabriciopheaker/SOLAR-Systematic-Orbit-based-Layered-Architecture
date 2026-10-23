import pytest

from nucleus.exceptions.validation_exception import ValidationException
from nucleus.upload.file_sanitizer import FileSanitizer, safe_filename
from nucleus.upload.file_validator import FileValidator
from nucleus.upload.upload_policy import UploadPolicy
from nucleus.upload.uploaded_file import UploadedFile


PDF = "application/pdf"

# Conteúdo com a assinatura REAL de PDF: sem isso a verificação
# de conteúdo reprova o arquivo.
PDF_CONTENT = b"%PDF-1.7\n1 0 obj\n"

PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

# O cenário do ataque: um script declarado como PDF.
SCRIPT = b"#!/bin/sh\nrm -rf /\n"


def _policy(**overrides) -> UploadPolicy:

    values = {
        "allowed_extensions": frozenset({".pdf"}),
        "allowed_content_types": frozenset({PDF}),
        "max_size_bytes": 1024,
        "max_files": 1,
    }

    values.update(overrides)

    return UploadPolicy(**values)


def _file(
    name: str = "contrato.pdf",
    content_type: str = PDF,
    content: bytes = PDF_CONTENT
) -> UploadedFile:

    return UploadedFile(
        name=name,
        content_type=content_type,
        content=content
    )


# ---------------------------------------------------------------------
# UploadedFile
# ---------------------------------------------------------------------

def test_uploaded_file_exposes_size_and_extension():

    file = _file()

    assert file.size == len(PDF_CONTENT)
    assert file.extension == ".pdf"


def test_uploaded_file_without_extension():

    assert _file(name="arquivo").extension == ""


# ---------------------------------------------------------------------
# FileSanitizer
# ---------------------------------------------------------------------

def test_sanitizer_strips_directory_traversal():

    sanitizer = FileSanitizer()

    sanitized = sanitizer.sanitize([_file(name="../../etc/passwd")])

    assert sanitized[0].name == "passwd"


def test_sanitizer_strips_windows_path():

    sanitizer = FileSanitizer()

    sanitized = sanitizer.sanitize(
        [_file(name="..\\..\\windows\\contrato.pdf")]
    )

    assert sanitized[0].name == "contrato.pdf"


def test_sanitizer_removes_forbidden_characters():

    sanitizer = FileSanitizer()

    sanitized = sanitizer.sanitize(
        [_file(name="rela<>:tório?.pdf")]
    )

    assert sanitized[0].name == "relatório.pdf"


def test_sanitizer_uses_fallback_for_empty_name():

    sanitizer = FileSanitizer()

    assert sanitizer.sanitize([_file(name="")])[0].name == "arquivo"
    assert sanitizer.sanitize([_file(name="../")])[0].name == "arquivo"

    assert safe_filename("..") == "arquivo"


def test_sanitizer_accepts_payload_map():

    sanitizer = FileSanitizer()

    sanitized = sanitizer.sanitize({"files": [_file()]})

    assert sanitized[0].name == "contrato.pdf"


# ---------------------------------------------------------------------
# FileValidator
# ---------------------------------------------------------------------

def test_validator_accepts_a_valid_upload():

    FileValidator(_policy()).validate([_file()])


def test_validator_rejects_missing_file():

    with pytest.raises(ValidationException):
        FileValidator(_policy()).validate([])


def test_validator_rejects_empty_file():

    with pytest.raises(ValidationException):
        FileValidator(_policy()).validate([_file(content=b"")])


def test_validator_rejects_file_above_max_size():

    with pytest.raises(ValidationException):
        FileValidator(
            _policy(max_size_bytes=5)
        ).validate([_file()])


def test_validator_rejects_disallowed_extension():

    with pytest.raises(ValidationException):
        FileValidator(
            _policy()
        ).validate([_file(name="script.exe")])


def test_validator_rejects_disallowed_content_type():

    with pytest.raises(ValidationException):
        FileValidator(
            _policy()
        ).validate([_file(content_type="application/zip")])


def test_validator_rejects_too_many_files():

    with pytest.raises(ValidationException):
        FileValidator(
            _policy(max_files=1)
        ).validate([_file(), _file()])


# o erro acumula TODOS os problemas de uma vez
def test_validator_reports_all_problems():

    with pytest.raises(ValidationException) as error:
        FileValidator(
            _policy(max_size_bytes=5)
        ).validate(
            [_file(name="script.exe", content_type="application/zip")]
        )

    message = str(error.value)

    assert "extensão" in message
    assert "tipo de conteúdo" in message
    assert "excede o tamanho" in message


# regra de NEGOCIO nao pertence ao Validator: um PDF
# estruturalmente valido passa, mesmo que o conteudo nao seja
# "um contrato valido" — isso e responsabilidade do UseCase.
def test_validator_does_not_check_business_rules():

    FileValidator(_policy()).validate(
        [_file(content=b"%PDF-1.7\nnao-e-um-contrato-valido")]
    )


# ---------------------------------------------------------------------
# Verificacao de CONTEUDO (magic bytes)
# ---------------------------------------------------------------------

# o cenario do ataque: script renomeado para .pdf
# A extensao e o MIME declarado mentem; a assinatura nao.
def test_validator_rejects_script_declared_as_pdf():

    with pytest.raises(ValidationException) as error:
        FileValidator(_policy()).validate(
            [_file(name="contrato.pdf", content=SCRIPT)]
        )

    message = str(error.value)

    assert "não corresponde ao tipo declarado" in message
    assert "application/pdf" in message


# conteudo de OUTRO tipo real tambem e reprovado
# (PNG declarado como PDF)
def test_validator_rejects_content_of_another_type():

    with pytest.raises(ValidationException):
        FileValidator(_policy()).validate(
            [_file(name="contrato.pdf", content=PNG)]
        )


# a verificacao pode ser desligada na policy
def test_content_verification_can_be_disabled():

    FileValidator(
        _policy(verify_content=False)
    ).validate([_file(content=SCRIPT)])


# ---------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------

def test_images_preset_accepts_a_real_png():

    FileValidator(UploadPolicy.images()).validate(
        [
            UploadedFile(
                name="foto.png",
                content_type="image/png",
                content=PNG
            )
        ]
    )


def test_images_preset_rejects_pdf_content_as_png():

    with pytest.raises(ValidationException):
        FileValidator(UploadPolicy.images()).validate(
            [
                UploadedFile(
                    name="foto.png",
                    content_type="image/png",
                    content=PDF_CONTENT
                )
            ]
        )


def test_documents_preset_accepts_a_real_pdf():

    FileValidator(UploadPolicy.documents()).validate([_file()])


def test_documents_preset_rejects_executable():

    with pytest.raises(ValidationException):
        FileValidator(UploadPolicy.documents()).validate(
            [_file(name="script.exe")]
        )
