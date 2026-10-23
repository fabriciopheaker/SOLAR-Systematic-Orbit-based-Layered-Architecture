import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.uploads_must_use_storage import (
    UploadsMustUseStorage
)
from nucleus.rules.scanner.upload_handling import UploadHandling


def _handling(primitives: set[str]) -> UploadHandling:

    return UploadHandling(
        controller="DocumentController",
        primitives=frozenset(primitives),
        file="planets/documents/controllers/document_controller.py",
        line=5
    )


# Controller que grava arquivo diretamente viola a regra
def test_controller_writing_file_directly_is_rejected():

    rule = UploadsMustUseStorage()

    with pytest.raises(SolarException):
        rule.validate(_handling({"open"}))


# Controller que usa write_bytes viola a regra
def test_controller_using_write_bytes_is_rejected():

    rule = UploadsMustUseStorage()

    with pytest.raises(SolarException):
        rule.validate(_handling({"write_bytes"}))


# Controller que usa shutil viola a regra
def test_controller_using_shutil_is_rejected():

    rule = UploadsMustUseStorage()

    with pytest.raises(SolarException):
        rule.validate(_handling({"shutil"}))


# Controller que inspeciona MIME type tambem e barrado
def test_controller_inspecting_mimetype_is_rejected():

    rule = UploadsMustUseStorage()

    with pytest.raises(SolarException):
        rule.validate(_handling({"mimetypes"}))


# Controller que delega o upload esta correto
def test_controller_delegating_upload_is_allowed():

    rule = UploadsMustUseStorage()

    rule.validate(_handling(set()))
