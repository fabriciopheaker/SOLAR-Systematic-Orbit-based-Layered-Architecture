from nucleus.rules.scanner.controller_security_scanner import (
    ControllerSecurityScanner
)


WITH_PRIMITIVES = """
import hashlib
import jwt


class AuthController:

    def login(self, payload):
        return jwt.encode({}, hashlib.sha256().hexdigest())
"""

WITH_ARCHITECTURE_COMPONENTS = """
from nucleus.security.password import Password
from nucleus.security.token import Token

from planets.auth.usecases.login import LoginUseCase


class AuthController:

    def login(self, payload):
        return LoginUseCase.execute(payload)
"""

NOT_A_CONTROLLER = """
import jwt


class AuthService:

    def login(self, payload):
        return jwt.encode({}, "x")
"""


def _scan(tmp_path, content: str):
    """
    Varre um Controller.

    O caminho importa: o scanner reconhece o Controller pelo LUGAR,
    e nao so pelo nome da classe.
    """

    controllers = tmp_path / "planets" / "auth" / "controllers"
    controllers.mkdir(parents=True)

    path = controllers / "auth_controller.py"
    path.write_text(content, encoding="utf-8")

    return ControllerSecurityScanner(tmp_path).scan()


# Classe terminando em "Controller" FORA de um modulo de Controller
# NAO e um Controller.
#
# Foi este o falso positivo real: a regra `RoutesMustPointToController`
# terminava em "Controller" e era auditada como Controller por tres
# regras ao mesmo tempo. Aqui ela importa `hashlib` e `jwt` de
# proposito: nem assim pode ser reportada.
def test_class_outside_a_controller_module_is_not_a_controller(tmp_path):

    path = tmp_path / "routes_must_point_to_controller.py"
    path.write_text(WITH_PRIMITIVES, encoding="utf-8")

    assert ControllerSecurityScanner(tmp_path).scan() == []


def test_scanner_lists_modules_known_by_controller(tmp_path):

    usages = _scan(tmp_path, WITH_PRIMITIVES)

    assert len(usages) == 1

    usage = usages[0]

    assert usage.controller == "AuthController"
    assert "hashlib" in usage.imports
    assert "jwt" in usage.imports


def test_scanner_lists_architecture_components(tmp_path):

    usage = _scan(tmp_path, WITH_ARCHITECTURE_COMPONENTS)[0]

    assert "nucleus" in usage.imports
    assert "planets" in usage.imports


# classe que nao e Controller nao e descrita
def test_scanner_ignores_non_controller_classes(tmp_path):

    assert _scan(tmp_path, NOT_A_CONTROLLER) == []
