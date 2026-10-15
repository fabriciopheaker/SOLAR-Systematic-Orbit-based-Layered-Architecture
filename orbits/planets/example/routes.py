"""
Rotas do Planet example.

A rota declara duas coisas, no MESMO lugar: para onde a requisição vai
(URL → Controller → método HTTP) e quem pode entrar (`sanitizer=` e
`validator=`). Quem lê este arquivo não precisa procurar a proteção em
outro lugar.

O `SolarBlueprint` é o que permite declarar os guardas aqui: o
`add_url_rule` do Flask não conhece esses dois keywords.
"""

from flask import Blueprint

from nucleus.middleware.solar_blueprint import SolarBlueprint

from orbits.planets.example.atmosphere.sanitizers.create_user_sanitizer import (  # noqa: E501
    CreateUserSanitizer,
)
from orbits.planets.example.atmosphere.validators.create_user_validator import (  # noqa: E501
    CreateUserValidator,
)
from orbits.planets.example.controllers.create_user_controller import (  # noqa: E501
    CreateUserController,
)


def routes() -> Blueprint:
    """
    Devolve o Blueprint do Planet.

    O contrato é sempre este: o Planet devolve o Blueprint dele, e
    quem registra na aplicação é o ponto central (`orbits/routes.py`).
    """

    # `SolarBlueprint`: é ele que aceita `sanitizer=` e `validator=` na
    # rota e liga o pipeline no `before_request` do Planet.
    blueprint = SolarBlueprint(
        "example",
        __name__,
        url_prefix="/examples"
    )

    # CRIAÇÃO DE USUÁRIO
    #
    # `add_url_rule` e não decorator: a declaração explícita é o que a
    # SOLAR-ARCH-016 exige. O alvo é um Controller (SOLAR-ARCH-017).
    #
    # Os guardas vêm declarados AQUI: quando o Controller for chamado,
    # o corpo já passou pelo Sanitizer e pelo Validator
    # (SOLAR-ARCH-013).
    #
    # Os três primeiros argumentos são coisas DIFERENTES:
    #
    #   "/users"                a URL  — o que o cliente digita
    #   "create_example_user"    o ENDPOINT — o nome INTERNO da rota
    #   CreateUserController.create   quem responde
    #
    # A URL é prefixada pelo Planet: `/examples` (do Blueprint) +
    # `/users` = `POST /examples/users`.
    #
    # O endpoint não é a URL: é o nome pelo qual o Flask conhece a rota
    # dentro da aplicação (`url_for("example.create_example_user")`), e
    # é a chave com que o `SolarBlueprint` guarda os guardas acima.
    blueprint.add_url_rule(
        "/users",
        "create_example_user",
        CreateUserController.create,
        methods=["POST"],
        sanitizer=CreateUserSanitizer,
        validator=CreateUserValidator,
    )

    return blueprint
