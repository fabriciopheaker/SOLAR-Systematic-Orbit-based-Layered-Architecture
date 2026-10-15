"""
A SOLAR-ARCH-014 sobre o RETORNO de um Controller.

A regra e de ANALISE ESTATICA: quem le o `return` e o
`ControllerReturnScanner`.
"""

import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.controller_must_return_resource import (
    ControllerMustReturnResource
)
from nucleus.rules.scanner.controller_return import ControllerReturn


def _target(resources: set[str] | None = None) -> ControllerReturn:
    """
    Um alvo de teste: o retorno de um metodo de Controller.
    """

    return ControllerReturn(
        controller="UserController",
        method="show",
        resources=frozenset(resources if resources is not None else set()),
        file="planets/user/controllers/user_controller.py",
        line=12
    )


# retorno que passa por Resource e valido
def test_return_through_resource_is_valid():

    rule = ControllerMustReturnResource()

    rule.validate(_target({"UserResource"}))


# retorno que NAO passa por Resource e invalido
def test_return_without_resource_is_invalid():

    rule = ControllerMustReturnResource()

    with pytest.raises(SolarException):
        rule.validate(_target())


# a mensagem diz QUAL metodo falhou e o que se espera dele
def test_message_names_the_controller_and_the_method():

    rule = ControllerMustReturnResource()

    with pytest.raises(SolarException) as caught:
        rule.validate(_target())

    message = str(caught.value)

    assert "UserController.show" in message
    assert "Resource" in message
