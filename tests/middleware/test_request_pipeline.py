import pytest

from nucleus.exceptions.contract_exception import ContractException
from nucleus.exceptions.solar_exception import SolarException
from nucleus.exceptions.validation_exception import ValidationException
from nucleus.contracts.http_input import HttpInput
from nucleus.contracts.sanitizer import Sanitizer
from nucleus.contracts.validator import Validator
from nucleus.middleware.request_pipeline import RequestPipeline


JSON = "application/json"
MULTIPART = "multipart/form-data"


class RecordingSanitizer(Sanitizer):

    def __init__(self, calls: list):

        self.calls = calls

    def sanitize(self, payload):

        self.calls.append("sanitize")

        return {
            "name": payload.get("name", "").strip().lower()
        }


class RecordingValidator(Validator):

    def __init__(self, calls: list):

        self.calls = calls
        self.received = None

    def validate(self, payload) -> None:

        self.calls.append("validate")
        self.received = payload

        if not payload.get("name"):
            raise ValidationException(
                "Campo 'name' é obrigatório.",
                code="INVALID_NAME"
            )


class FileSanitizer(Sanitizer):

    def __init__(self):

        self.sanitized = False

    def sanitize(self, payload):

        self.sanitized = True

        return payload


class FileValidator(Validator):

    def __init__(self):

        self.validated = False

    def validate(self, payload) -> None:

        self.validated = True


# JSON: o pipeline VALIDA ANTES de sanitizar
def test_json_input_validates_then_sanitizes():

    calls: list = []
    validator = RecordingValidator(calls)

    http_input = HttpInput(
        method="POST",
        name="/users",
        content_type=JSON,
        sanitizer=RecordingSanitizer(calls),
        validator=validator
    )

    result = RequestPipeline().handle(
        http_input,
        {"name": "  Ana  "}
    )

    assert calls == ["validate", "sanitize"]
    assert result == {"name": "ana"}
    assert validator.received == {"name": "  Ana  "}


# NAO e limitado ao POST: PUT JSON passa pelo mesmo pipeline
def test_put_json_input_runs_the_pipeline():

    calls: list = []

    http_input = HttpInput(
        method="PUT",
        name="/users/1",
        content_type=JSON,
        sanitizer=RecordingSanitizer(calls),
        validator=RecordingValidator(calls)
    )

    result = RequestPipeline().handle(
        http_input,
        {"name": "  Ana  "}
    )

    assert calls == ["validate", "sanitize"]
    assert result == {"name": "ana"}


# multipart/upload usa FileSanitizer + FileValidator
def test_multipart_input_runs_file_guards():

    sanitizer = FileSanitizer()
    validator = FileValidator()

    http_input = HttpInput(
        method="POST",
        name="/documents",
        content_type=MULTIPART,
        sanitizer=sanitizer,
        validator=validator
    )

    payload = {"files": [b"conteudo"]}

    result = RequestPipeline().handle(http_input, payload)

    assert sanitizer.sanitized is True
    assert validator.validated is True
    assert result == payload


# entrada que transporta dados SEM guardas e rejeitada (013)
def test_input_with_data_without_guards_is_rejected():

    http_input = HttpInput(
        method="PUT",
        name="/users/1",
        content_type=JSON
    )

    with pytest.raises(SolarException):
        RequestPipeline().handle(http_input, {"name": "ana"})


# entrada sem dados externos passa direto, sem sanitizar/validar
def test_input_without_data_passes_through_untouched():

    payload = {"qualquer": "coisa"}

    http_input = HttpInput(method="GET", name="/solar/health")

    assert RequestPipeline().handle(http_input, payload) is payload


# falha de validacao se propaga
def test_validation_failure_propagates():

    calls: list = []

    http_input = HttpInput(
        method="POST",
        name="/users",
        content_type=JSON,
        sanitizer=RecordingSanitizer(calls),
        validator=RecordingValidator(calls)
    )

    with pytest.raises(ValidationException):
        RequestPipeline().handle(http_input, {})


# campo ausente e recusado ANTES de o Sanitizer rodar
#
# E a razao da ordem: sanitizar campo que nao chegou quebra, e a
# validacao perde a chance de dizer o que faltou.
def test_missing_field_is_rejected_before_sanitizing():

    calls: list = []

    http_input = HttpInput(
        method="POST",
        name="/users",
        content_type=JSON,
        sanitizer=RecordingSanitizer(calls),
        validator=RecordingValidator(calls)
    )

    with pytest.raises(ValidationException):
        RequestPipeline().handle(http_input, {"outro": "valor"})

    assert calls == ["validate"]


# O pipeline roda em TEMPO DE EXECUCAO: exige a IMPLEMENTACAO,
# nao o nome declarado usado na validacao estatica.
def test_pipeline_requires_real_implementations():

    http_input = HttpInput(
        method="POST",
        name="/documents",
        content_type=MULTIPART,
        sanitizer="FileSanitizer",
        validator="FileValidator"
    )

    with pytest.raises(ContractException):
        RequestPipeline().handle(http_input, {"files": []})
