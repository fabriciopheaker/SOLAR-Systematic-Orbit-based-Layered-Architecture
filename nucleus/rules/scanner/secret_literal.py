# Contexto da SOLAR-ARCH-020: a DESCRIÇÃO de um literal atribuído
# a um nome sensível.
#
# `frozen` porque é fato consumado — o scanner achou, a regra lê.
# Ninguém altera o achado no meio do caminho.
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretLiteral:
    """
    Representa um VALOR LITERAL associado a um nome sensível.

    O SecretScanner produz esta estrutura quando encontra:

        SECRET_KEY = "abc123"
        DATABASE_PASSWORD = "root"
        connect(password="root")

    O scanner produz apenas nomes que casam com o vocabulário de
    segredos e apenas valores LITERAIS não vazios. A decisão de
    violação é da Rule SOLAR-ARCH-020.

    name:
        Nome do alvo (variável, constante ou keyword argument).

    value:
        O valor literal encontrado (nunca é ecoado em log).

    file:
        Arquivo onde o segredo foi encontrado.

    line:
        Linha onde o segredo foi encontrado.

    suppressed:
        O trecho está anotado com o marcador de exceção
        (`# solar:allow-secret`).

    default:
        O valor é um DEFAULT que espera vir do ambiente (começa
        com o prefixo `SOLAR_DEFAULT`). Não é segredo.

    O scanner apenas DESCREVE o que achou; quem decide ignorar é
    a Rule SOLAR-ARCH-020.
    """

    name: str
    value: str
    file: str
    line: int

    # As duas marcas que isentam o achado, e ambas são decididas
    # pelo scanner — não pela regra: `suppressed` (marcador no
    # código) e `default` (valor começa com SOLAR_DEFAULT). O
    # padrão `False` é o lado seguro: sem marca, o achado vale.
    suppressed: bool = False
    default: bool = False
