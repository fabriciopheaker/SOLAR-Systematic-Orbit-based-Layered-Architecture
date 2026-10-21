"""
Rotas do Planet user.

Este é o módulo de rotas do Planet — o lugar onde as rotas dele
moram (SOLAR-ROF-004).
"""

from nucleus.middleware.solar_blueprint import SolarBlueprint


def routes() -> Blueprint:
    """
    Devolve o Blueprint do Planet.

    O contrato é sempre este: o Planet devolve o Blueprint dele, e
    quem registra na aplicação é o ponto central
    (`orbits/routes.py`). O Planet NÃO conhece a aplicação — é o
    que permite registrá-lo em outro conjunto sem mudar nada aqui.

    Ainda não há rota nenhuma: a primeira entra quando existir.
    """

    # O prefixo fica com o PLANET: `/users/...` para este. Assim o
    # Planet decide o próprio caminho, e não quem o agrega.
    return SolarBlueprint("user", __name__, url_prefix="/users")
