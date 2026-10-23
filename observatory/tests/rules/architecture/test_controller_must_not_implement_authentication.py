import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.controller_must_not_implement_authentication import (
    ControllerMustNotImplementAuthentication
)
from nucleus.rules.scanner.controller_security_usage import (
    ControllerSecurityUsage
)


def _usage(imports: set[str]) -> ControllerSecurityUsage:

    return ControllerSecurityUsage(
        controller="AuthController",
        imports=frozenset(imports),
        file="planets/auth/controllers/auth_controller.py",
        line=6
    )


# Controller que implementa hash/mesmo token viola a regra
@pytest.mark.parametrize(
    "package",
    [
        "hashlib",
        "bcrypt",
        "jwt",
        "jose",
        "secrets",
        "hmac",
        "passlib",
        "cryptography",
    ]
)
def test_controller_using_auth_primitive_is_rejected(package):

    rule = ControllerMustNotImplementAuthentication()

    with pytest.raises(SolarException):
        rule.validate(_usage({package}))


# Controller que usa os componentes da arquitetura esta correto
def test_controller_using_architecture_components_is_allowed():

    rule = ControllerMustNotImplementAuthentication()

    rule.validate(
        _usage({"nucleus", "planets"})
    )


# Controller sem modulos de autenticacao esta correto
def test_controller_without_security_modules_is_allowed():

    rule = ControllerMustNotImplementAuthentication()

    rule.validate(_usage({"os", "json"}))
