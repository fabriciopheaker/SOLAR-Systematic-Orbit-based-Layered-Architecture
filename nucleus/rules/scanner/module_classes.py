# Contexto da SOLAR-ARCH-032: as classes declaradas em um arquivo.
#
# Dois níveis porque a regra precisa dos dois: `ModuleClasses` diz
# QUANTAS classes o arquivo tem, e `DeclaredClass` diz QUAL e onde —
# é a linha da segunda classe que a mensagem da violação aponta.
from dataclasses import dataclass


@dataclass(frozen=True)
class DeclaredClass:
    """
    Uma classe declarada em um arquivo.

    name:
        Nome da classe (ex.: "UserModel").

    line:
        Linha da declaração.
    """

    name: str

    # Guardada para a violação poder apontar o "arquivo:linha" exato
    # da classe excedente, em vez de só o nome do arquivo.
    line: int


@dataclass(frozen=True)
class ModuleClasses:
    """
    Descreve as CLASSES declaradas em UM arquivo.

    module:
        Caminho pontuado do módulo
        (ex.: "orbits.database.models.user_model").

    file:
        Caminho do arquivo relativo à raiz
        (ex.: "orbits/database/models/user_model.py").

    classes:
        Classes declaradas no arquivo, em ordem de linha.

    O scanner DESCREVE o que cada arquivo declara — inclusive os
    arquivos com uma única classe, e inclusive classes que não são
    Model. Quem decide quantas classes um Model pode ter por
    arquivo é a Rule SOLAR-ARCH-032.
    """

    module: str
    file: str

    # Tupla e não conjunto: a mensagem da violação cita as classes
    # na ORDEM do arquivo, e "Primeira, Segunda" é mais útil para
    # quem vai corrigir do que uma ordem qualquer.
    classes: tuple[DeclaredClass, ...]

    def names(self) -> tuple[str, ...]:
        """
        Nomes das classes declaradas.
        """

        return tuple(item.name for item in self.classes)
