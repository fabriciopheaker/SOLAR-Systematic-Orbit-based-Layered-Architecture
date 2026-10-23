from nucleus.rules.scanner.upload_handling_scanner import (
    UploadHandlingScanner
)


MANIPULATING = """
import shutil
import mimetypes


class DocumentController:

    def upload(self, arquivo):
        shutil.copy(arquivo, "/tmp/documento.pdf")
        mimetypes.guess_type(arquivo.filename)
        with open("documento.pdf", "wb") as target:
            target.write_bytes(arquivo.read())
"""

DELEGATING = """
from planets.documents.usecases.upload_document import UploadDocumentUseCase


class DocumentController:

    def upload(self, arquivo):
        return UploadDocumentUseCase.execute(arquivo)
"""

NOT_A_CONTROLLER = """
import shutil


class DocumentService:

    def upload(self, arquivo):
        shutil.copy(arquivo, "/tmp/x.pdf")
"""


def _scan(tmp_path, content: str):

    controllers = tmp_path / "planets" / "documents" / "controllers"
    controllers.mkdir(parents=True)

    path = controllers / "document_controller.py"
    path.write_text(content, encoding="utf-8")

    return UploadHandlingScanner(tmp_path).scan()


def test_scanner_lists_file_primitives(tmp_path):

    handlings = _scan(tmp_path, MANIPULATING)

    assert len(handlings) == 1

    handling = handlings[0]

    assert handling.controller == "DocumentController"
    assert "shutil" in handling.primitives
    assert "mimetypes" in handling.primitives
    assert "open" in handling.primitives
    assert "write_bytes" in handling.primitives


# Controller que delega nao usa primitivos de arquivo
def test_scanner_reports_no_primitives_when_delegating(tmp_path):

    handling = _scan(tmp_path, DELEGATING)[0]

    assert handling.primitives == frozenset()


# classe que nao e Controller nao e descrita
def test_scanner_ignores_non_controller_classes(tmp_path):

    assert _scan(tmp_path, NOT_A_CONTROLLER) == []
