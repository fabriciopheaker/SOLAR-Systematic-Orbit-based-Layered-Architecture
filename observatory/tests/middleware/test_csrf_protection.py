import pytest

from nucleus.exceptions.security_exception import SecurityException
from nucleus.middleware.csrf_protection import CsrfProtection


class FakeClock:
    """
    Relógio controlável — o TTL vira determinístico.
    """

    def __init__(self, now: float = 0.0):
        self.value = now

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _protection(clock=None) -> CsrfProtection:

    return CsrfProtection(
        clock=clock or FakeClock(),
        token_factory=lambda: "token-fixo"
    )


# ---------------------------------------------------------------------
# Emissão e conferência
# ---------------------------------------------------------------------

def test_issued_token_is_accepted():

    csrf = _protection()
    session = "sessao-1"

    token = csrf.issue(session)

    assert token == "token-fixo"
    assert csrf.is_valid(session, token) is True
    assert csrf.validate(session, token) is None


def test_token_from_another_session_is_rejected():

    csrf = _protection()

    csrf.issue("sessao-1")
    csrf.issue("sessao-2")

    assert csrf.is_valid("sessao-1", "outro-token") is False


def test_session_without_token_is_rejected():

    csrf = _protection()

    assert csrf.is_valid("sessao-desconhecida", "qualquer") is False


@pytest.mark.parametrize("token", [None, "", "   ", 42, b"bytes"])
def test_malformed_tokens_are_rejected(token):

    csrf = _protection()
    session = "sessao-1"

    csrf.issue(session)

    assert csrf.is_valid(session, token) is False


def test_validate_raises_with_the_right_code():

    csrf = _protection()

    with pytest.raises(SecurityException) as error:
        csrf.validate("sessao-1", "token-errado")

    assert error.value.code == CsrfProtection.INVALID_TOKEN


# ---------------------------------------------------------------------
# Expiração
# ---------------------------------------------------------------------

def test_token_expires():

    clock = FakeClock()
    csrf = _protection(clock)
    session = "sessao-1"

    token = csrf.issue(session)

    clock.advance(3599)

    assert csrf.is_valid(session, token) is True


def test_token_is_rejected_after_the_ttl():

    clock = FakeClock()
    csrf = _protection(clock)
    session = "sessao-1"

    token = csrf.issue(session)

    clock.advance(3601)

    assert csrf.is_valid(session, token) is False
    assert csrf.token(session) is None


# reemitir renova o prazo e troca o token
def test_reissuing_replaces_the_token():

    clock = FakeClock()
    csrf = CsrfProtection(
        clock=clock,
        token_factory=iter(["primeiro", "segundo"]).__next__
    )

    session = "sessao-1"

    first = csrf.issue(session)

    clock.advance(3000)

    second = csrf.issue(session)

    assert first != second
    assert csrf.is_valid(session, first) is False
    assert csrf.is_valid(session, second) is True


# ---------------------------------------------------------------------
# Descarte
# ---------------------------------------------------------------------

def test_reset_discards_the_token():

    csrf = _protection()
    session = "sessao-1"

    token = csrf.issue(session)

    csrf.reset(session)

    assert csrf.is_valid(session, token) is False


# ---------------------------------------------------------------------
# Constantes usadas pelo cliente
# ---------------------------------------------------------------------

def test_field_and_header_are_declared():

    assert CsrfProtection.FIELD == "csrf_token"
    assert CsrfProtection.HEADER == "X-CSRF-Token"


# o token padrao e aleatorio e nao previsivel
def test_default_token_is_random():

    csrf = CsrfProtection()

    primeiro = csrf.issue("sessao-1")
    segundo = csrf.issue("sessao-2")

    assert primeiro != segundo
    assert len(primeiro) >= 32
