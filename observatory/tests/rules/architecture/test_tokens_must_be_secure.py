import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.tokens_must_be_secure import (
    TokensMustBeSecure
)
from nucleus.rules.scanner.token_usage import TokenUsage


def _usage(
    operation: str = "encode",
    algorithm: str | None = "HS256",
    verifies_signature: bool | None = None,
    has_expiration: bool | None = True
) -> TokenUsage:

    return TokenUsage(
        operation=operation,
        algorithm=algorithm,
        verifies_signature=verifies_signature,
        has_expiration=has_expiration,
        file="planets/auth/token_gateway.py",
        line=10
    )


# token assinado com algoritmo seguro, com expiracao e verificado
def test_secure_token_is_allowed():

    rule = TokensMustBeSecure()

    rule.validate(_usage())

    rule.validate(
        _usage(operation="decode", has_expiration=None)
    )


# algoritmo "none" (token sem assinatura) e rejeitado
def test_unsigned_algorithm_is_rejected():

    rule = TokensMustBeSecure()

    with pytest.raises(SolarException):
        rule.validate(_usage(algorithm="none"))


# algoritmo NAO declarado explicitamente e rejeitado
def test_missing_algorithm_is_rejected():

    rule = TokensMustBeSecure()

    with pytest.raises(SolarException):
        rule.validate(_usage(algorithm=None))


# token emitido sem expiracao e rejeitado
def test_token_without_expiration_is_rejected():

    rule = TokensMustBeSecure()

    with pytest.raises(SolarException):
        rule.validate(_usage(has_expiration=False))


# verificacao de assinatura desativada na leitura e rejeitada
def test_decode_without_signature_verification_is_rejected():

    rule = TokensMustBeSecure()

    with pytest.raises(SolarException):
        rule.validate(
            _usage(
                operation="decode",
                algorithm="HS256",
                verifies_signature=False,
                has_expiration=None
            )
        )


# payload nao literal (nao verificavel) nao inventa violacao
def test_unverifiable_expiration_does_not_violate():

    rule = TokensMustBeSecure()

    rule.validate(_usage(has_expiration=None))
