# Exceção de persistência/banco.
#
# Existe para o `except` ficar ESPECÍFICO: quem captura
# `DatabaseException` sabe que o problema é o banco, e não a
# validação da entrada ou o armazenamento de arquivo.
from .solar_exception import SolarException


class DatabaseException(SolarException):
    """
    Exceção relacionada a falhas de persistência ou conexão
    com o banco de dados.
    """

    # Sem corpo de propósito: o que importa é o TIPO. A mensagem
    # vem de quem levanta a exceção (o driver de banco).
    pass