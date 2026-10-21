"""
Rotas do Planet solar.

O Planet `solar` é o Planet da PRÓPRIA PLATAFORMA: responde sobre a
aplicação, e não sobre um módulo de negócio. Hoje é só a verificação
de saúde. A página inicial da API — os dados que a interface Vue
consome — entra AQUI quando existir, sem Planet novo e sem camada
nova.

A rota declara o ESSENCIAL: URL → Controller → método HTTP — e, quando
há, quem protege a entrada (`sanitizer=` e `validator=`).
"""

from flask import Blueprint

from nucleus.middleware.solar_blueprint import SolarBlueprint

from orbits.planets.solar.controllers.health_controller import (
    HealthController,
)


def routes() -> Blueprint:
    """
    Devolve o Blueprint do Planet.

    O contrato é sempre este: o Planet devolve o Blueprint dele, e
    quem registra na aplicação é o ponto central
    (`orbits/routes.py`).
    """

    # O prefixo fica com o PLANET: `/solar/...` para este. Assim o
    # Planet decide o próprio caminho, e não quem o agrega.
    blueprint = SolarBlueprint(
        "solar",
        __name__,
        url_prefix="/solar"
    )

    # VERIFICAÇÃO DE SAÚDE
    #
    # GET não transporta dados, então a rota NÃO declara guarda: não
    # há corpo para limpar nem campo para exigir (SOLAR-ROF-001).
    #
    # `add_url_rule` e não decorator: a declaração explícita é o que
    # a SOLAR-ROF-004 exige. O alvo é um Controller (SOLAR-ROF-005).
    blueprint.add_url_rule(
        "/health",
        "health",
        HealthController.status,
        methods=["GET"],
    )

    return blueprint
