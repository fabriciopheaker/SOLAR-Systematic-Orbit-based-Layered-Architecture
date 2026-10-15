"""
O Controller do fluxo de criação de usuário.

O Controller da SOLAR não é uma view do framework: ele é a peça que
ORQUESTRA a requisição.

    Request → Input → UseCase → Resource → Response

O que NÃO mora aqui: validação, sanitização, regra de negócio, SQL.
A entrada é tratada pela Atmosphere do Planet, e o que este método lê
já passou pela fronteira.
"""

from flask import g

from orbits.planets.example.controllers.inputs.create_user_input import (
    CreateUserInput,
)
from orbits.planets.example.resources.user_resource import UserResource
from orbits.planets.example.usecases.create_user_usecase import (
    create_user_use_case,
)


class CreateUserController:
    """
    Cria o usuário a partir do corpo da requisição.

    A rota aponta para `CreateUserController.create` (SOLAR-ARCH-017)
    e o retorno passa por um Resource (SOLAR-ARCH-014).

    `@staticmethod` porque a rota é registrada como
    `CreateUserController.create`: o Flask chama a função direto, sem
    instância no meio — e sem receber argumento nenhum.
    """

    @staticmethod
    def create() -> tuple[dict, int]:
        """
        Cria o usuário e devolve `(corpo, status)` — o que o Flask
        espera de uma view.
        """

        # O corpo JÁ TRATADO pela Atmosphere.
        #
        # Ler do `g` é o mecanismo do Flask para dado por REQUISIÇÃO:
        # a Atmosphere escreve, o Controller lê. Aqui não se valida
        # nem se limpa nada — o que chega já passou pela fronteira.
        data = g.solar_data

        # O corpo vira CONTRATO nomeado: é o que o UseCase recebe, e
        # o que impede o dicionário do HTTP de circular pelo domínio.
        user_input = CreateUserInput(data)

        output = create_user_use_case().execute(user_input)

        # 201: o recurso foi CRIADO. O 200 diria "aqui está o que já
        # existia", que é outra coisa.
        return UserResource.to_object(output), 201
