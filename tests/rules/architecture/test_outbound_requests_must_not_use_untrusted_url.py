import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.outbound_requests_must_not_use_untrusted_url import (
    OutboundRequestsMustNotUseUntrustedUrl
)
from nucleus.rules.scanner.outbound_request import OutboundRequest


def _request(
    names: set[str] | frozenset = frozenset(),
    url: str = "..."
) -> OutboundRequest:

    return OutboundRequest(
        package="requests",
        url=url,
        names=frozenset(names),
        file="satellites/integrations/http_gateway.py",
        line=27
    )


# ---------------------------------------------------------------------
# Confiável
# ---------------------------------------------------------------------

def test_literal_url_is_allowed():

    rule = OutboundRequestsMustNotUseUntrustedUrl()

    rule.validate(_request())


# constante: pela convenção do projeto, UPPER_CASE
def test_constant_names_are_allowed():

    rule = OutboundRequestsMustNotUseUntrustedUrl()

    rule.validate(_request({"BASE_URL"}))
    rule.validate(_request({"API_URL", "BASE_URL"}))


def test_configuration_names_are_allowed():

    rule = OutboundRequestsMustNotUseUntrustedUrl()

    rule.validate(_request({"environment"}))
    rule.validate(_request({"settings"}))


# ---------------------------------------------------------------------
# Não confiável
# ---------------------------------------------------------------------

# URL escolhida por quem chamou
def test_request_derived_url_is_rejected():

    rule = OutboundRequestsMustNotUseUntrustedUrl()

    with pytest.raises(SolarException):
        rule.validate(_request({"request", "args"}))


# variável crua: nao se sabe o que carrega
def test_lowercase_variable_is_rejected():

    rule = OutboundRequestsMustNotUseUntrustedUrl()

    with pytest.raises(SolarException):
        rule.validate(_request({"url"}, url="url"))


# atributo de instancia tambem precisa ser confiavel
def test_instance_attribute_is_rejected():

    rule = OutboundRequestsMustNotUseUntrustedUrl()

    with pytest.raises(SolarException):
        rule.validate(_request({"base_url"}, url="self.base_url"))


# ---------------------------------------------------------------------
# Mensagem
# ---------------------------------------------------------------------

def test_message_lists_the_untrusted_names():

    rule = OutboundRequestsMustNotUseUntrustedUrl()

    with pytest.raises(SolarException) as error:
        rule.validate(_request({"host", "BASE_URL"}))

    message = str(error.value)

    assert "SOLAR-ARCH-030" in message
    assert "'host'" in message
    assert "'BASE_URL'" not in message
    assert "UrlGuard" in message
    assert "http_gateway.py:27" in message
