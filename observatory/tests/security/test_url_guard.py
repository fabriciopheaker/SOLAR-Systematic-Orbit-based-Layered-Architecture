import pytest

from nucleus.exceptions.security_exception import SecurityException
from nucleus.security.url_guard import UrlGuard


# ---------------------------------------------------------------------
# Permitido
# ---------------------------------------------------------------------

def test_public_https_url_is_allowed():

    assert UrlGuard().is_allowed("https://api.exemplo.com/users") is True


def test_subdomain_of_an_allowed_host_is_allowed():

    guard = UrlGuard(allowed_hosts=["exemplo.com"])

    assert guard.is_allowed("https://api.exemplo.com/users") is True
    assert guard.is_allowed("https://exemplo.com/") is True


# ---------------------------------------------------------------------
# Esquema
# ---------------------------------------------------------------------

def test_plain_http_is_rejected_by_default():

    guard = UrlGuard()

    with pytest.raises(SecurityException) as error:
        guard.validate("http://api.exemplo.com")

    assert error.value.code == UrlGuard.DISALLOWED_SCHEME


def test_file_scheme_is_rejected():

    guard = UrlGuard()

    with pytest.raises(SecurityException):
        guard.validate("file:///etc/passwd")


def test_scheme_can_be_extended_explicitly():

    guard = UrlGuard(allowed_schemes=["https", "http"])

    assert guard.is_allowed("http://api.exemplo.com") is True


# ---------------------------------------------------------------------
# Endereço interno (SSRF)
# ---------------------------------------------------------------------

# metadata service das nuvens: o alvo classico de SSRF
def test_metadata_address_is_rejected():

    guard = UrlGuard()

    with pytest.raises(SecurityException) as error:
        guard.validate("https://169.254.169.254/latest/meta-data/")

    assert error.value.code == UrlGuard.PRIVATE_ADDRESS


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.5",
        "192.168.1.10",
        "172.16.4.2",
        "0.0.0.0",
    ]
)
def test_private_ipv4_addresses_are_rejected(address):

    guard = UrlGuard()

    with pytest.raises(SecurityException) as error:
        guard.validate(f"https://{address}/interno")

    assert error.value.code == UrlGuard.PRIVATE_ADDRESS


def test_loopback_ipv6_is_rejected():

    guard = UrlGuard()

    with pytest.raises(SecurityException):
        guard.validate("https://[::1]/interno")


# ---------------------------------------------------------------------
# Host e credenciais
# ---------------------------------------------------------------------

def test_host_outside_the_allowlist_is_rejected():

    guard = UrlGuard(allowed_hosts=["exemplo.com"])

    with pytest.raises(SecurityException) as error:
        guard.validate("https://outro.com/dados")

    assert error.value.code == UrlGuard.DISALLOWED_HOST


# a lista e a defesa principal: sem ela, nomes publicos passam
def test_without_allowlist_any_public_host_is_allowed():

    guard = UrlGuard()

    assert guard.is_allowed("https://qualquer-dominio-publico.com") is True


def test_credentials_in_url_are_rejected():

    guard = UrlGuard()

    with pytest.raises(SecurityException) as error:
        guard.validate("https://usuario:senha@api.exemplo.com")

    assert error.value.code == UrlGuard.URL_CREDENTIALS


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        None,
        "https://",
        "sem-esquema",
    ]
)
def test_malformed_urls_are_rejected(url):

    guard = UrlGuard()

    with pytest.raises(SecurityException):
        guard.validate(url)


def test_is_allowed_never_raises():

    guard = UrlGuard()

    assert guard.is_allowed("file:///etc/passwd") is False
    assert guard.is_allowed("https://169.254.169.254/") is False
