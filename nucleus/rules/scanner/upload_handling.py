# Contexto da SOLAR-ARCH-025: primitivos de arquivo usados por um
# Controller.
#
# Um Controller não manipula arquivo — ele entrega o arquivo à
# abstração de Storage. O scanner descreve os primitivos que achou;
# a regra é que acusa.
from dataclasses import dataclass


@dataclass(frozen=True)
class UploadHandling:
    """
    Descreve os PRIMITIVOS DE ARQUIVO usados por um Controller.

    O scanner produz esta estrutura para cada Controller — uma
    classe terminada em "Controller" DENTRO de um módulo de
    Controller (ver `controller_module`) — e lista as operações de
    arquivo encontradas no seu corpo:

        controller = "DocumentController"
        primitives = {"open", "write_bytes"}

    Um Controller CORRETO não manipula arquivo: ele entrega o
    arquivo à abstração de armazenamento (Storage).

    primitives:
        Operações de arquivo usadas (vazio quando o Controller
        não toca em arquivo).

    file / line:
        Local da declaração da classe.
    """

    controller: str

    # Vazio significa "não toca em arquivo", que é o caso correto.
    primitives: frozenset[str]

    file: str
    line: int
