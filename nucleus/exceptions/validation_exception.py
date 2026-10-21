# Exceção de validação da entrada.
#
# É a exceção que o contrato `Validator` promete lançar. O
# ErrorHandler a converte em resposta 400 com o código do problema —
# e o detalhe do que faltou NUNCA vai para o cliente (SOLAR-SEG-008).
from .solar_exception import SolarException


class ValidationException(SolarException):
    """
    Exceção relacionada a falhas de validação.
    """

    # Sem corpo de propósito: o que importa é o TIPO. A mensagem
    # vem de quem levanta a exceção (o Validator).
    pass