# Contexto da SOLAR-ARCH-019: a estrutura de um Planet.
#
# O scanner só LISTA o que existe na raiz do Planet (`files` e
# `directories`); a regra é que sabe qual é o conjunto exigido. Por
# isso o contexto é uma descrição crua, e não um veredito.
from dataclasses import dataclass


@dataclass(frozen=True)
class PlanetStructure:
    """
    Descreve a estrutura de um Planet.

    name:
        Nome do Planet (ex.: "user").

    path:
        Caminho do Planet relativo à raiz do projeto
        (ex.: "planets/user").

    files:
        Nomes dos ARQUIVOS na raiz do Planet.

    directories:
        Nomes dos DIRETÓRIOS na raiz do Planet.

    O scanner produz esta estrutura; as Rules decidem se ela é
    arquiteturalmente válida.
    """

    name: str
    path: str

    # Vazios por padrão (e não obrigatórios): um Planet ainda em
    # construção não pode quebrar o scanner. Quem reclama da
    # ausência é a regra, com a mensagem certa.
    files: frozenset[str] = frozenset()
    directories: frozenset[str] = frozenset()
