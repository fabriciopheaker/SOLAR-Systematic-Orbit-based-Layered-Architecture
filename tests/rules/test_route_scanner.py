from pathlib import Path

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

HTTP_VERB_DECORATOR_ROUTES = """
@router.get("/users")
def list_users():
    return []
"""

LAMBDA_ROUTE = """
api.add_url_rule(
    "/api",
    "home",
    lambda: {"ok": True},
    methods=["GET"],
)
"""

COMPOSITION = """
from flask import Blueprint

from planets.auth.routes import auth_routes
from planets.user.routes import user_routes

api = Blueprint("api", __name__)

for route in [
    auth_routes,
    user_routes,
]:
    api.register_blueprint(route)
"""

NO_ROUTING = """
from planets.user.controllers.user_controller import UserController


USERS = [
    UserController.list,
    UserController.show,
]

DEFAULTS = {
    "page": 1,
    "size": 20,
}
"""


def _write(root: Path, relative: str, content: str) -> None:

    path = root / relative

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(content, encoding="utf-8")


def _scan_single(tmp_path: Path, relative: str, content: str):

    _write(tmp_path, relative, content)

    return RouteScanner(tmp_path).scan()


# add_url_rule registrado em um Blueprint e reconhecido
def test_scanner_detects_add_url_rule(tmp_path):

    declarations = _scan_single(
        tmp_path,
        "planets/auth/routes.py",
        AUTH_ROUTES
    )

    assert len(declarations) == 1

    declaration = declarations[0]

    assert declaration.module == "planets.auth.routes"
    assert declaration.file == "planets/auth/routes.py"
    assert declaration.style == RouteDeclaration.REGISTRATION
    assert declaration.mechanism == "add_url_rule"
    assert declaration.target == "AuthController.login"


# decorators de roteamento sao reconhecidos
def test_scanner_detects_route_decorator(tmp_path):

    declarations = _scan_single(
        tmp_path,
        "planets/user/routes.py",
        DECORATOR_ROUTES
    )

    assert len(declarations) == 1
    assert declarations[0].style == RouteDeclaration.DECORATOR
    assert declarations[0].mechanism == "route"
    assert declarations[0].target == "list_users"


# decorators de verbo HTTP tambem sao reconhecidos
def test_scanner_detects_http_verb_decorator(tmp_path):

    declarations = _scan_single(
        tmp_path,
        "planets/user/routes.py",
        HTTP_VERB_DECORATOR_ROUTES
    )

    assert len(declarations) == 1
    assert declarations[0].style == RouteDeclaration.DECORATOR
    assert declarations[0].mechanism == "get"


# lambda como alvo e identificada como alvo nao qualificado
def test_scanner_marks_lambda_target(tmp_path):

    declarations = _scan_single(
        tmp_path,
        "orbits/routes/api.py",
        LAMBDA_ROUTE
    )

    assert len(declarations) == 1
    assert declarations[0].target == "<lambda>"


# 9. composicao central (register_blueprint) nao declara rota
def test_composition_does_not_declare_routes(tmp_path):

    declarations = _scan_single(
        tmp_path,
        "orbits/routes/api.py",
        COMPOSITION
    )

    assert declarations == []


# 10. a arquitetura nao exige register_*_routes():
# o modulo de rotas declara e o scanner reconhece sem qualquer
# funcao de registro por Planet.
def test_route_module_does_not_need_register_function(tmp_path):

    declarations = _scan_single(
        tmp_path,
        "planets/auth/routes.py",
        AUTH_ROUTES
    )

    assert declarations
    assert "register_auth_routes" not in AUTH_ROUTES


# listas/dicts no modulo NAO geram declaracoes de rota
def test_plain_collections_do_not_declare_routes(tmp_path):

    declarations = _scan_single(
        tmp_path,
        "planets/user/routes.py",
        NO_ROUTING
    )

    assert declarations == []


# nenhuma rota: scan vazio
def test_scanner_without_routes_returns_empty(tmp_path):

    _write(tmp_path, "planets/user/service.py", "VALUE = 1\n")

    assert RouteScanner(tmp_path).scan() == []
