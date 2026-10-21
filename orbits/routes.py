"""
O ponto central das rotas da aplicação.

A SOLAR-ROF-004 diz onde rota pode morar: em
`planets/<planeta>/routes.py` ou aqui. Não existe um terceiro
lugar — é o que impede rota declarada no meio de um service, de um
repository ou de um controller.

Este módulo faz uma coisa, e só uma: agregar os Blueprints dos
Planets. NÃO há rota própria aqui — até a verificação de saúde
pertence a um Planet (o `solar`), e é o que mantém a regra sem
nenhuma exceção.
"""

from flask import Blueprint

from orbits.planets.auth import routes as auth_routes
from orbits.planets.example import routes as example_routes
from orbits.planets.solar import routes as solar_routes
from orbits.planets.user import routes as user_routes


def routes() -> Blueprint:
    """
    Devolve o Blueprint com as rotas da aplicação.

    Este módulo MONTA; quem registra na aplicação é o Kernel. A
    separação é o que permite montar tudo em teste sem subir
    servidor.
    """

    # Um `Blueprint` do Flask, sem adaptador nenhum: a proteção de
    # entrada é responsabilidade de cada Planet, na Atmosphere dele.
    blueprint = Blueprint("orbits", __name__)

    # ROTA DE SAÚDE
    #
    # Deixou de morar aqui: ela pertence ao Planet `solar`, que é o
    # Planet da própria plataforma. Aqui não sobra nenhuma rota
    # avulsa — e é isso que faz a SOLAR-ROF-004 valer sem exceção.

    # PLANETS
    #
    # Um Planet novo entra por uma linha DAQUI. Este é o único
    # lugar do projeto que conhece a lista de Planets: o Kernel
    # registra o conjunto, e não cada um.
    blueprint.register_blueprint(auth_routes.routes())
    blueprint.register_blueprint(user_routes.routes())

    # O Planet `solar` é o da própria plataforma: responde sobre a
    # aplicação, e não sobre um módulo de negócio. É onde mora a
    # verificação de saúde.
    blueprint.register_blueprint(solar_routes.routes())

    # O Planet `example` é o fluxo completo de referência: criação de
    # usuário passando por todas as camadas. Ele entra aqui como
    # qualquer outro — é o que prova que o ponto central não precisa
    # conhecer o que o Planet faz.
    blueprint.register_blueprint(example_routes.routes())

    return blueprint
