# Exceção de armazenamento de arquivos.
#
# O contrato do StorageDriver promete lançá-la quando o arquivo não
# existe (`read`) — é ela que permite ao chamador distinguir
# "não existe" de "não consegui falar com o armazenamento".
from .solar_exception import SolarException


class StorageException(SolarException):
    """
    Exceção relacionada a falhas de armazenamento de arquivos.
    """

    # Sem corpo de propósito: o que importa é o TIPO. A mensagem
    # vem de quem levanta a exceção (o driver de armazenamento).
    pass
