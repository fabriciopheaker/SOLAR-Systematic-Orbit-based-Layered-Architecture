# Contexto da SOLAR-ARCH-022: os módulos que um Controller conhece.
#
# O scanner lista TODOS os imports do arquivo, sem opinião. Quem
# decide quais são proibidos é a regra: a lista de proibidos é
# decisão de arquitetura, não de análise estática.
from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerSecurityUsage:
    """
    Descreve os módulos que um Controller conhece diretamente.

    O ControllerSecurityScanner produz esta estrutura para cada
    Controller — uma classe terminada em "Controller" DENTRO de um
    módulo de Controller (ver `controller_module`):

        controller = "AuthController"
        imports    = {"jwt", "hashlib", "os"}

    O scanner lista TODOS os módulos importados no arquivo; é a
    Rule SOLAR-ARCH-022 que decide quais são proibidos.

    controller:
        Nome da classe Controller.

    imports:
        Módulos de topo importados no arquivo do Controller.

    file / line:
        Local da declaração da classe.
    """

    controller: str

    # Imports do ARQUIVO (Python não tem import por classe), e por
    # isso todos os Controllers do módulo compartilham o conjunto.
    imports: frozenset[str]

    file: str
    line: int
