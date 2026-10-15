# Exceção do mecanismo de Broadcast.
#
# Não acrescenta campo nem comportamento — existe para o `except`
# poder ser específico: capturar `SolarException` pegaria também
# erro de validação e de banco.
from .solar_exception import SolarException


class BroadcastException(SolarException):
    """
    Exceção relacionada ao mecanismo de Broadcast da SOLAR.

    Representa falhas ocorridas durante publicação,
    inscrição ou remoção de listeners.
    """

    # Sem corpo de propósito: o que importa é o TIPO. A mensagem
    # vem de quem levanta a exceção (o driver de broadcast).
    pass