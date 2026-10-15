# Contrato de uma regra arquitetural da SOLAR.
#
# Uma Rule só decide POLÍTICA: recebe um contexto já montado — pelo
# scanner, quando a análise é estática; pela Atmosphere, quando é
# em tempo de execução — e diz se aquilo viola a arquitetura. A
# regra NÃO varre arquivos e NÃO monta contexto.
#
# O sinal de violação é sempre o mesmo: `SolarException`. É ela que
# o ProjectValidator recolhe para virar violação do relatório.
#
# ATENÇÃO: `code` e `description` estão declarados aqui como
# `property`, mas as regras concretas os implementam como MÉTODO, e
# é assim que os chamadores usam (`rule.code()`). A ABC aceita
# porque só exige que o nome exista.
from abc import ABC, abstractmethod


class Rule(ABC):

    @property
    @abstractmethod
    def code(self) -> str:
        """
          Identificador único da regra.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """
          Descrição da regra arquitetural.
        """
        raise NotImplementedError

    # `context` sem tipo anotado de propósito: o tipo é DIFERENTE
    # em cada regra (SecretLiteral, SecretOccurrence, Route, ...),
    # e é a subclasse que documenta qual contexto ela espera.
    @abstractmethod
    def validate(self, context) -> None:
        """
          Verifica se a regra está sendo respeitada.
        """
        raise NotImplementedError