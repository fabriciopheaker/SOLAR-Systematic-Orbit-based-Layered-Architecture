"""
Onde mora o módulo de um Controller.

Este critério e COMPARTILHADO pelas regras 014, 022, 025 e 026: as
quatro precisam concordar sobre o que e um Controller, senao uma peca
seria Controller para uma regra e nao para outra.

O que se prova aqui e o que o sufixo do NOME nao resolvia: uma classe
terminando em "Controller" fora de `planets/<planeta>/controllers/`
NAO e um Controller.
"""

from pathlib import Path

from nucleus.rules.scanner.controller_module import is_controller_module


# arquivo dentro de `planets/<planeta>/controllers/` e um modulo de
# Controller — a estrutura da SOLAR-ARCH-019
def test_file_inside_controllers_is_a_controller_module():

    file = Path("orbits/planets/user/controllers/user_controller.py")

    assert is_controller_module(file) is True


# `controller.py` solto NAO e modulo de Controller: sem o Planet, nao
# ha Controller.
#
# Era exatamente o caso do `orbits/health/controller.py`, que existiu
# ate virar o Planet `solar`: tinha o nome, nao o lugar.
def test_controller_file_outside_a_planet_is_not_a_controller_module():

    assert is_controller_module(Path("orbits/health/controller.py")) is False


# `controllers/` FORA de `planets/` tambem nao vale: a estrutura so
# conta dentro do Planet
def test_controllers_outside_planets_is_not_a_controller_module():

    file = Path("orbits/health/controllers/health_controller.py")

    assert is_controller_module(file) is False


# arquivo solto NAO e modulo de Controller, mesmo com o nome parecido
#
# Foi este o caso real: a regra `routes_must_point_to_controller.py`
# era lida como Controller por tres regras diferentes.
def test_loose_file_is_not_a_controller_module():

    file = Path("nucleus/rules/architecture/routes_must_point_to_controller.py")

    assert is_controller_module(file) is False


# arquivo que mora fora de `controllers/` tambem nao e
def test_file_outside_controllers_is_not_a_controller_module():

    file = Path("orbits/planets/user/usecases/create_user.py")

    assert is_controller_module(file) is False
