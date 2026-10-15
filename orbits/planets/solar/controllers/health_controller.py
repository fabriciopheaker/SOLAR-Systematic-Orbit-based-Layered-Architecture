"""
O Controller da verificação de saúde da aplicação.

O Controller da SOLAR não é uma view do framework: ele é a peça que
orquestra a requisição. Aqui não há muito o que orquestrar — a
verificação responde sobre a APLICAÇÃO, e não sobre um módulo de
negócio.

Este Planet é o da própria plataforma, e é por isso que ele não tem
negócio nenhum: o que não pertence a um Planet de domínio mora aqui.
"""

from orbits.planets.solar.resources.health_resource import HealthResource


class HealthController:
    """
    Verifica se a aplicação está de pé.

    A rota aponta para `HealthController.status` (SOLAR-ARCH-017) e o
    retorno passa por um Resource (SOLAR-ARCH-014).

    GET não transporta dados, então não há Atmosphere nesta rota: não
    há corpo para validar nem para limpar.

    A verificação é mínima de propósito: ela existe para provar que o
    caminho inteiro está de pé — rota, Controller, Resource e
    resposta.
    """

    @staticmethod
    def status() -> tuple[dict, int]:
        """
        Representa a verificação de saúde.
        """

        # O `{}` é o dado do Controller: a verificação não depende de
        # nada da requisição.
        return HealthResource.to_object({}), 200
