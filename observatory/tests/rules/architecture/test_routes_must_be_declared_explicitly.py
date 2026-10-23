import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.routes_must_be_declared_explicitly import (
    RoutesMustBeDeclaredExplicitly
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

DECORATOR_ROUTES = """
from flask import Flask

app = Flask(__name__)


@app.route("/users", methods=["GET"])
def list_users():
    return []
"""


def _declaration(
    style: str,
    mechanism: str,
    target: str | None
) -> RouteDeclaration:

    return RouteDeclaration(
        module="planets.user.routes",
        file="planets/user/routes.py",
        line=10,
        style=style,
        mechanism=mechanism,
        target=target
    )


def _scan(tmp_path, content: str) -> list[RouteDeclaration]:

    path = tmp_path / "routes.py"
    path.write_text(content, encoding="utf-8")

    return RouteScanner(tmp_path).scan()


# 4. decorators de roteamento sao rejeitados
def test_route_declared_by_decorator_is_rejected(tmp_path):

    declarations = _scan(tmp_path, DECORATOR_ROUTES)

    assert declarations

    rule = RoutesMustBeDeclaredExplicitly()

    with pytest.raises(SolarException):
        rule.validate(declarations[0])


# 4. decorator de verbo HTTP tambem e rejeitado
def test_http_verb_decorator_is_rejected():

    rule = RoutesMustBeDeclaredExplicitly()

    with pytest.raises(SolarException):
        rule.validate(
            _declaration(
                RouteDeclaration.DECORATOR,
                "get",
                "list_users"
            )
        )


# 2. e 3. registro explicito (add_url_rule em Blueprint) e permitido
def test_explicit_registration_is_allowed(tmp_path):

    declarations = _scan(tmp_path, AUTH_ROUTES)

    assert declarations

    rule = RoutesMustBeDeclaredExplicitly()

    for declaration in declarations:
        rule.validate(declaration)


# registro explicito direto tambem e permitido
def test_add_url_rule_declaration_is_allowed():

    rule = RoutesMustBeDeclaredExplicitly()

    rule.validate(
        _declaration(
            RouteDeclaration.REGISTRATION,
            "add_url_rule",
            "AuthController.login"
        )
    )
