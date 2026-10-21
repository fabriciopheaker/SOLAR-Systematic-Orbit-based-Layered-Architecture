import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.routes_must_point_to_controller import (
    RoutesMustPointToController
)
from nucleus.rules.scanner.route_declaration import RouteDeclaration
from nucleus.rules.scanner.route_scanner import RouteScanner


AUTH_ROUTES = """
from flask import Blueprint

from planets.auth.controllers.auth_controller import AuthController

auth_routes = Blueprint("auth", __name__)

auth_routes.add_url_rule(
    "/login",
    "login",
    AuthController.login,
    methods=["POST"],
)
"""


def _registration(target: str | None) -> RouteDeclaration:

    return RouteDeclaration(
        module="planets.auth.routes",
        file="planets/auth/routes.py",
        line=10,
        style=RouteDeclaration.REGISTRATION,
        mechanism="add_url_rule",
        target=target
    )


def _scan(tmp_path, content: str) -> list[RouteDeclaration]:

    path = tmp_path / "routes.py"
    path.write_text(content, encoding="utf-8")

    return RouteScanner(tmp_path).scan()


# 1. e 8. rota apontando para Controller e permitida
def test_route_pointing_to_controller_is_allowed(tmp_path):

    declarations = _scan(tmp_path, AUTH_ROUTES)

    assert declarations

    rule = RoutesMustPointToController()

    for declaration in declarations:
        rule.validate(declaration)


# 8. Controller em forma direta e permitido
def test_direct_controller_reference_is_allowed():

    rule = RoutesMustPointToController()

    rule.validate(
        _registration("UserController.create")
    )


# 5. Route → UseCase e rejeitado
def test_route_pointing_to_usecase_is_rejected():

    rule = RoutesMustPointToController()

    with pytest.raises(SolarException):
        rule.validate(
            _registration("CreateUserUseCase.execute")
        )


# 6. Route → Repository e rejeitado
def test_route_pointing_to_repository_is_rejected():

    rule = RoutesMustPointToController()

    with pytest.raises(SolarException):
        rule.validate(
            _registration("UserRepository.find")
        )


# 7. Route → Entity e rejeitado
def test_route_pointing_to_entity_is_rejected():

    rule = RoutesMustPointToController()

    with pytest.raises(SolarException):
        rule.validate(
            _registration("User")
        )


# rota apontando para Service e rejeitada
def test_route_pointing_to_service_is_rejected():

    rule = RoutesMustPointToController()

    with pytest.raises(SolarException):
        rule.validate(
            _registration("UserService.create")
        )


# rota com lambda (health/home) e rejeitada
def test_route_with_lambda_target_is_rejected():

    rule = RoutesMustPointToController()

    with pytest.raises(SolarException):
        rule.validate(
            _registration("<lambda>")
        )


# rota sem alvo identificavel e rejeitada
def test_route_without_target_is_rejected():

    rule = RoutesMustPointToController()

    with pytest.raises(SolarException):
        rule.validate(
            _registration(None)
        )


# ESCOPO: rotas por decorator sao responsabilidade da SOLAR-ROF-004
def test_decorator_declarations_are_out_of_scope():

    declaration = RouteDeclaration(
        module="planets.user.routes",
        file="planets/user/routes.py",
        line=10,
        style=RouteDeclaration.DECORATOR,
        mechanism="route",
        target="list_users"
    )

    rule = RoutesMustPointToController()

    rule.validate(declaration)
