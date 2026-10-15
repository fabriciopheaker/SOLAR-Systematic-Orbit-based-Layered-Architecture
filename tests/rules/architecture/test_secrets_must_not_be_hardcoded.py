import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.secrets_must_not_be_hardcoded import (
    SecretsMustNotBeHardcoded
)
from nucleus.rules.scanner.secret_literal import SecretLiteral


def _secret(name: str, value: str = "segredo") -> SecretLiteral:

    return SecretLiteral(
        name=name,
        value=value,
        file="planets/user/config.py",
        line=3
    )


# segredo hardcoded viola a regra
def test_hardcoded_secret_is_rejected():

    rule = SecretsMustNotBeHardcoded()

    with pytest.raises(SolarException):
        rule.validate(_secret("SECRET_KEY"))


# credenciais de banco hardcoded violam a regra
def test_hardcoded_database_password_is_rejected():

    rule = SecretsMustNotBeHardcoded()

    with pytest.raises(SolarException):
        rule.validate(_secret("DATABASE_PASSWORD", "root"))


# tokens internos hardcoded violam a regra
def test_hardcoded_token_is_rejected():

    rule = SecretsMustNotBeHardcoded()

    with pytest.raises(SolarException):
        rule.validate(_secret("API_TOKEN", "987654"))


# nomes que nao sao segredos sao ignorados pela regra
def test_non_secret_name_is_ignored():

    rule = SecretsMustNotBeHardcoded()

    rule.validate(_secret("password_field", "senha"))

    rule.validate(_secret("TOKEN_EXPIRATION", "1h"))

    rule.validate(_secret("USER_NAME", "ana"))


# valor marcado como DEFAULT nao viola: o campo espera o ambiente
def test_default_value_is_allowed():

    rule = SecretsMustNotBeHardcoded()

    rule.validate(
        SecretLiteral(
            name="SECRET_KEY",
            value="SOLAR_DEFAULT",
            file="nucleus/security/identity.py",
            line=25,
            default=True
        )
    )


# a excecao explicita nao viola: o valor nao e segredo
def test_suppressed_secret_is_allowed():

    rule = SecretsMustNotBeHardcoded()

    rule.validate(
        SecretLiteral(
            name="SECRET_KEY",
            value="SECRET_KEY",
            file="nucleus/security/identity.py",
            line=25,
            suppressed=True
        )
    )
