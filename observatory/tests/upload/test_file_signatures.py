from nucleus.upload.file_signatures import (
    canonical,
    is_verifiable,
    matches,
    sniff
)


PDF = b"%PDF-1.7\n1 0 obj\n"
PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF"
GIF = b"GIF89a\x01\x00\x01\x00"
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 "
ZIP = b"PK\x03\x04\x14\x00\x00\x00"
OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1\x00"
SCRIPT = b"#!/bin/sh\nrm -rf /\n"


# ---------------------------------------------------------------------
# sniff
# ---------------------------------------------------------------------

def test_sniff_detects_pdf():

    assert sniff(PDF) == "application/pdf"


def test_sniff_detects_images():

    assert sniff(PNG) == "image/png"
    assert sniff(JPEG) == "image/jpeg"
    assert sniff(GIF) == "image/gif"
    assert sniff(WEBP) == "image/webp"


def test_sniff_detects_containers():

    assert sniff(ZIP) == "application/zip"
    assert sniff(OLE) == "application/x-ole-storage"


def test_sniff_does_not_recognize_a_script():

    assert sniff(SCRIPT) is None


# ---------------------------------------------------------------------
# canonical
# ---------------------------------------------------------------------

def test_canonical_normalizes_aliases():

    assert canonical("image/jpg") == "image/jpeg"

    assert canonical(
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ) == "application/zip"

    assert canonical("application/pdf") == "application/pdf"


# ---------------------------------------------------------------------
# is_verifiable
# ---------------------------------------------------------------------

def test_types_with_signature_are_verifiable():

    assert is_verifiable("application/pdf") is True
    assert is_verifiable("image/png") is True


def test_types_without_signature_are_not_verifiable():

    assert is_verifiable("text/plain") is False


# ---------------------------------------------------------------------
# matches — o núcleo da proteção
# ---------------------------------------------------------------------

def test_content_matching_declared_type():

    assert matches(PDF, "application/pdf") is True
    assert matches(PNG, "image/png") is True


# o cenario do ataque: script renomeado e declarado como PDF
def test_script_declared_as_pdf_does_not_match():

    assert matches(SCRIPT, "application/pdf") is False


# conteudo de outro tipo tambem nao casa
def test_pdf_declared_as_png_does_not_match():

    assert matches(PDF, "image/png") is False


# .docx e um container ZIP: casa pelo tipo canonico
def test_docx_declared_with_zip_content_matches():

    assert matches(
        ZIP,
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ) is True


# tipo sem assinatura nao e verificavel: nao ha como reprovar
def test_unverifiable_type_always_matches():

    assert matches(SCRIPT, "text/plain") is True
