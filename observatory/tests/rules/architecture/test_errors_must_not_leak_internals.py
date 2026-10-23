import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.errors_must_not_leak_internals import (
    ErrorsMustNotLeakInternals
)
from nucleus.rules.scanner.error_exposure import ErrorExposure


def _exposure(
    detail: str = "str",
    destination: str = "response"
) -> ErrorExposure:

    return ErrorExposure(
        handler="error",
        detail=detail,
        destination=destination,
        file="orbits/planets/documents/controllers/document_controller.py",
        line=42
    )


# detalhe interno voltando na resposta viola a regra
def test_detail_in_response_is_rejected():

    rule = ErrorsMustNotLeakInternals()

    with pytest.raises(SolarException):
        rule.validate(_exposure())


# traceback na resposta e o caso mais grave
def test_traceback_in_response_is_rejected():

    rule = ErrorsMustNotLeakInternals()

    with pytest.raises(SolarException):
        rule.validate(_exposure(detail="traceback"))


# o mesmo detalhe indo para o LOG e o comportamento correto
def test_detail_in_log_is_allowed():

    rule = ErrorsMustNotLeakInternals()

    rule.validate(_exposure(detail="f-string", destination="log"))


# destino nao comprovado nao e violacao: o detalhe pode ter virado
# registro de relatorio
# (foi o falso positivo que o proprio ProjectValidator produziu)
def test_unproven_destination_is_allowed():

    rule = ErrorsMustNotLeakInternals()

    rule.validate(_exposure(detail="str", destination="local"))


# a mensagem aponta o local e o caminho correto
def test_message_points_to_the_location():

    rule = ErrorsMustNotLeakInternals()

    with pytest.raises(SolarException) as error:
        rule.validate(_exposure(detail="args"))

    message = str(error.value)

    assert "SOLAR-SEG-008" in message
    assert "args" in message
    assert "document_controller.py:42" in message
    assert "log" in message
