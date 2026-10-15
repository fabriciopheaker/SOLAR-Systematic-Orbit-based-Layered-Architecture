# Exceção de segurança da aplicação.
#
# Cobre token inválido/expirado, falha de CSRF, bloqueio por
# tentativas e política de segurança violada — tudo o que o
# `nucleus.security` e o middleware recusam.
from .solar_exception import SolarException


class SecurityException(SolarException):
    """
    Exceção relacionada a falhas de segurança da aplicação.
    """

    # Sem corpo de propósito: o que importa é o TIPO. A mensagem
    # vem de quem levanta a exceção.
    pass