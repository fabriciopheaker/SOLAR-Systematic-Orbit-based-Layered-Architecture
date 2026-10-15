from nucleus.exceptions.solar_exception import SolarException
from nucleus.middleware.error_handler import ErrorHandler


def test_payload_has_only_safe_fields():

    payload = ErrorHandler().handle(
        RuntimeError('relation "users" does not exist')
    )

    assert set(payload) == {"code", "message", "reference"}


# o detalhe interno NAO aparece na resposta
def test_internal_detail_does_not_reach_the_payload():

    payload = ErrorHandler().handle(
        RuntimeError('relation "users" does not exist')
    )

    assert "relation" not in payload["message"]
    assert "users" not in str(payload)
    assert payload["message"] == ErrorHandler.GENERIC_MESSAGE


# o codigo da excecao da SOLAR e preservado: e util e nao expoe
# nada de interno
def test_solar_code_is_preserved():

    payload = ErrorHandler().handle(
        SolarException("arquivo invalido", code="INVALID_UPLOAD")
    )

    assert payload["code"] == "INVALID_UPLOAD"
    assert payload["message"] == ErrorHandler.GENERIC_MESSAGE


def test_internal_code_is_used_as_fallback():

    payload = ErrorHandler().handle(ValueError("qualquer coisa"))

    assert payload["code"] == ErrorHandler.INTERNAL_CODE


# a referencia liga a resposta ao log
def test_reference_is_stable_between_payload_and_detail():

    handler = ErrorHandler()
    error = RuntimeError("falha")

    payload = handler.handle(error)

    assert payload["reference"] in handler.detail(error)


def test_reference_can_be_injected():

    handler = ErrorHandler(identify=lambda: "referencia-fixa")

    payload = handler.handle(RuntimeError("falha"))

    assert payload["reference"] == "referencia-fixa"


# o detalhe interno e bem-vindo no LOG
def test_detail_keeps_the_internal_information():

    detail = ErrorHandler().detail(
        RuntimeError('relation "users" does not exist')
    )

    assert "RuntimeError" in detail
    assert 'relation "users"' in detail


# modo desenvolvimento: expor e uma decisao explicita
def test_exposed_details_are_opt_in():

    payload = ErrorHandler(expose_details=True).handle(
        RuntimeError('relation "users" does not exist')
    )

    assert 'relation "users"' in payload["message"]
