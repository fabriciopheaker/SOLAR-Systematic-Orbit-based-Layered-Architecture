"""
O que o scanner de retorno de Controller descreve.

O que se prova aqui e o FATO que a SOLAR-ARCH-014 le: o retorno passa
por uma chamada ao Resource?
"""

from nucleus.rules.scanner.controller_return_scanner import (
    ControllerReturnScanner
)


WITH_RESOURCE = """
from planets.example.resources.user_resource import UserResource


class CreateUserController:

    @staticmethod
    def create():
        return UserResource.to_object(output), 201
"""

WITHOUT_RESOURCE = """
class CreateUserController:

    @staticmethod
    def create():
        return {"id": 1}, 201
"""

WITH_VARIABLE = """
class CreateUserController:

    @staticmethod
    def create():
        resource = UserResource
        return resource.to_object(output), 201
"""

WITH_PRIVATE_HELPER = """
class CreateUserController:

    @staticmethod
    def create():
        return UserResource.to_object(output), 201

    @staticmethod
    def _helper():
        return "sem resource"
"""

NOT_A_CONTROLLER = """
class UserService:

    @staticmethod
    def run():
        return {"id": 1}
"""


def _scan(tmp_path, content: str):
    """
    Varre um modulo de Controller.

    O caminho importa: o scanner reconhece o Controller pelo LUGAR,
    e nao so pelo nome da classe.
    """

    controllers = tmp_path / "planets" / "user" / "controllers"
    controllers.mkdir(parents=True)

    path = controllers / "user_controller.py"
    path.write_text(content, encoding="utf-8")

    return ControllerReturnScanner(tmp_path).scan()


# o scanner reporta o nome do Resource chamado no retorno
def test_scanner_finds_the_resource_call(tmp_path):

    targets = _scan(tmp_path, WITH_RESOURCE)

    assert len(targets) == 1

    target = targets[0]

    assert target.controller == "CreateUserController"
    assert target.method == "create"
    assert target.resources == {"UserResource"}
    assert target.uses_resource() is True


# retorno sem Resource: o alvo existe, mas nao passa por Resource
def test_return_without_resource_is_reported(tmp_path):

    target = _scan(tmp_path, WITHOUT_RESOURCE)[0]

    assert target.resources == frozenset()
    assert target.uses_resource() is False


# Resource guardado numa variavel tambem conta
def test_resource_in_a_variable_is_recognized(tmp_path):

    target = _scan(tmp_path, WITH_VARIABLE)[0]

    assert target.resources == {"resource"}
    assert target.uses_resource() is True


# metodo privado NAO e alvo: ele nao responde requisicao
def test_private_method_is_not_a_target(tmp_path):

    targets = _scan(tmp_path, WITH_PRIVATE_HELPER)

    assert [target.method for target in targets] == ["create"]


# classe sem o sufixo nao e Controller
def test_class_without_the_suffix_is_not_a_controller(tmp_path):

    assert _scan(tmp_path, NOT_A_CONTROLLER) == []


# o LUGAR identifica a peca: uma classe que termina em "Controller"
# fora de um modulo de Controller NAO e um Controller
#
# Foi exatamente este o falso positivo que o scanner produziu na
# primeira versao: a regra `RoutesMustPointToController` terminava em
# "Controller" e foi acusada pela SOLAR-ARCH-014.
def test_class_outside_a_controller_module_is_not_a_controller(tmp_path):

    path = tmp_path / "routes_must_point_to_controller.py"
    path.write_text(WITHOUT_RESOURCE, encoding="utf-8")

    assert ControllerReturnScanner(tmp_path).scan() == []


# `controller.py` FORA de `planets/<planeta>/controllers/` NAO e um
# modulo de Controller: sem o Planet, nao ha Controller.
#
# Era exatamente o caso do `orbits/health/controller.py`, que existiu
# ate virar o Planet `solar`: tinha o nome, nao o lugar.
def test_controller_file_outside_a_planet_is_not_a_controller(tmp_path):

    path = tmp_path / "health" / "controller.py"
    path.parent.mkdir(parents=True)
    path.write_text(WITH_RESOURCE, encoding="utf-8")

    assert ControllerReturnScanner(tmp_path).scan() == []
