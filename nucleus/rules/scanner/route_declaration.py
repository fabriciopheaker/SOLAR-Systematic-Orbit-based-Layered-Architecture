# Contexto das regras de roteamento (SOLAR-ARCH-016, 017 e 018).
#
# É uma DESCRIÇÃO da declaração: onde está, como foi feita e para quem
# aponta. Nenhuma das três regras olha o mesmo pedaço, mas as três leem
# esta mesma estrutura — ver o docstring da classe.
from dataclasses import dataclass


@dataclass(frozen=True)
class RouteDeclaration:
    """
    Representa uma declaração de rota encontrada no código-fonte.

    O RouteScanner produz esta estrutura; as Rules decidem se a
    declaração é arquiteturalmente permitida.

    module:
        Módulo onde a rota foi declarada (ex.: "planets.auth.routes").

    file:
        Arquivo onde a rota foi declarada
        (ex.: "planets/auth/routes.py").

    line:
        Linha da declaração.

    style:
        Forma de declaração:
            DECORATOR    → declarada por decorator de framework
            REGISTRATION → registrada explicitamente

    mechanism:
        Mecanismo utilizado (ex.: "route", "get", "add_url_rule").

    target:
        Alvo da rota, quando identificável (ex.: "AuthController.login").
        None quando não há alvo declarado.
    """

    module: str
    file: str
    line: int

    # `style` recebe uma das duas constantes logo abaixo, e é por ele
    # que as regras 016/017 se decidem — cada uma cuida de um estilo.
    style: str

    # O nome do que foi usado (`route`, `get`, `add_url_rule`): é ele
    # que aparece na mensagem da violação.
    mechanism: str

    # Padrão `None` porque lambda e expressão inline não têm alvo — e
    # é justamente esse caso que a SOLAR-ARCH-017 acusa.
    target: str | None = None

    # Rota declarada por decorator do framework — PROIBIDA pela
    # SOLAR-ARCH-016.
    DECORATOR = "decorator"

    # Rota registrada explicitamente — o único estilo aceito pela
    # SOLAR-ARCH-016, e o único que a SOLAR-ARCH-017 avalia.
    REGISTRATION = "registration"
