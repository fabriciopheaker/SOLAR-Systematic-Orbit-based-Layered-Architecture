# Exceção de contrato arquitetural violado.
#
# É o sinal de que uma peça não respeitou o contrato da SOLAR —
# Controller sem Resource, UseCase com estrutura anônima na
# fronteira. Diferente das demais: aqui o erro é de DESENHO, e não
# de dado recebido.
from .solar_exception import SolarException


class ContractException(SolarException):
    """
    Exceção lançada quando um componente não respeita
    um contrato definido pela arquitetura SOLAR.
    """

    # Sem corpo de propósito: o que importa é o TIPO.
    pass