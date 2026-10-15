# Contrato de UseCase: a responsabilidade de aplicação de um Planet.
#
# O par de contratos (entrada e saída nomeadas) é o que a
# SOLAR-ARCH-015 defende: sem ele, o formato da resposta vira detalhe
# interno e qualquer mudança interna quebra o cliente.
from abc import ABC, abstractmethod


class UseCase(ABC):
    """
    Contrato de UseCase da SOLAR.

    Um UseCase representa uma responsabilidade de aplicação
    de um Planet.

    A entrada e a saída (CONTRATO) devem ser estruturas NOMEADAS
    (Input, Output, Entity). Estruturas anônimas (dict, list, tuple,
    set) como contrato violam a SOLAR-ARCH-015.

    Coleções anônimas são permitidas no processamento INTERNO:
    iteração, agregação, transformação, filtros e acumuladores
    não violam a regra.

    A implementação concreta deve declarar seu
    ResponsibilityContract e expô-lo para validação.
    """

    # `request` é a estrutura NOMEADA de entrada (Input), e não o
    # corpo cru da requisição: converter HTTP em Input é trabalho do
    # Controller, e é o que mantém o UseCase fora do framework.
    @abstractmethod
    def execute(self, request):
        """
        Executa a responsabilidade do UseCase.

        O request recebido deve ser uma estrutura nomeada,
        nunca uma estrutura anônima.
        """
        raise NotImplementedError
