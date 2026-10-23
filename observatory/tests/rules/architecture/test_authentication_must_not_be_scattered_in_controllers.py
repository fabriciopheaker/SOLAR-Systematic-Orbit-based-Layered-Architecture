import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.authentication_must_not_be_scattered_in_controllers import (
    AuthenticationMustNotBeScatteredInControllers
)
from nucleus.rules.scanner.controller_auth_checks import (
    ControllerAuthChecks
)


def _usage(checks: set[str]) -> ControllerAuthChecks:

    return ControllerAuthChecks(
        controller="DocumentController",
        checks=frozenset(checks),
        file="planets/documents/controllers/document_controller.py",
        line=5
    )


# Controller que verifica autenticacao viola a regra
def test_controller_checking_authentication_is_rejected():

    rule = AuthenticationMustNotBeScatteredInControllers()

    with pytest.raises(SolarException):
        rule.validate(_usage({"current_user"}))


# abort(401) espalhado no Controller viola a regra
def test_controller_with_abort_is_rejected():

    rule = AuthenticationMustNotBeScatteredInControllers()

    with pytest.raises(SolarException):
        rule.validate(_usage({"abort(401)"}))


# verificacao de permissao tambem e barrada
def test_controller_checking_permission_is_rejected():

    rule = AuthenticationMustNotBeScatteredInControllers()

    with pytest.raises(SolarException):
        rule.validate(_usage({"has_permission", "abort(403)"}))


# Controller que delega o fluxo esta correto
def test_controller_delegating_is_allowed():

    rule = AuthenticationMustNotBeScatteredInControllers()

    rule.validate(_usage(set()))
