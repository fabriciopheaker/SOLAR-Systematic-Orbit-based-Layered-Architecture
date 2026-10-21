# Onde mora o módulo de um Controller.
#
# Compartilhado pelas regras que falam de Controller — SOLAR-ROF-002, SOLAR-SEG-003, SOLAR-SEG-005 e
# SOLAR-SEG-006 —, porque as quatro precisam CONCORDAR sobre o que é um
# Controller: uma peça que é Controller para uma regra e não é para
# outra produz exatamente a contradição que a arquitetura existe para
# evitar.
#
# ⚠️ O QUE ESTE MÓDULO CONSERTA. Antes, cada scanner reconhecia o
# Controller pelo SUFIXO DO NOME da classe. O sufixo pega o que NÃO é
# Controller: a própria regra `RoutesMustPointToController` termina em
# "Controller" e era auditada como se fosse um Controller de Planet por
# três regras ao mesmo tempo. Ela passava por sorte — não importa nada
# da lista proibida da SOLAR-SEG-003, não faz verificação de autenticação e não
# manipula arquivo. Bastava um `import hashlib` para virar violação de
# uma regra que não tem nada a ver com ela.
#
# O NOME não basta: o LUGAR diz o que a peça é. Um Controller mora em
# `planets/<planeta>/controllers/` — a estrutura que a SOLAR-ROF-006
# já exige de todo Planet. Fora do Planet não há Controller: um
# `controller.py` solto em outro diretório tem o nome, mas não tem o
# lugar, e é o lugar que a arquitetura usa para saber o que a peça é.
from pathlib import Path


# Onde os Planetas moram (SOLAR-ROF-004).
PLANETS_DIRECTORY = "planets"

# Diretório onde os Controllers de um Planet moram (SOLAR-ROF-006).
CONTROLLERS_DIRECTORY = "controllers"

# Segmentos mínimos para caber `planets/<planeta>/controllers/<a>.py`.
REQUIRED_SEGMENTS = 4


def is_controller_module(file: Path) -> bool:
    """
    Indica se o arquivo é um módulo de Controller.

    O critério é o LUGAR do arquivo, e não o nome da classe: quem
    decide se uma classe é Controller é onde ela foi declarada.

    O LUGAR é a estrutura que a SOLAR-ROF-006 exige de todo Planet:

        planets/<planeta>/controllers/<arquivo>.py

    Um `controllers/` fora de `planets/` não vale, e um
    `controller.py` solto também não: sem o Planet, não há
    Controller.
    """

    # O diretório imediatamente antes do arquivo é `controllers/`,
    # e antes do nome do planeta vem `planets/`.
    parts = file.parts

    if len(parts) < REQUIRED_SEGMENTS:
        return False

    return (
        parts[-2] == CONTROLLERS_DIRECTORY
        and parts[-4] == PLANETS_DIRECTORY
    )
