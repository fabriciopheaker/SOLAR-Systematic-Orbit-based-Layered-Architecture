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


# Convenção de identificação das regras.
#
# O código tem o formato `SOLAR-<CATEGORIA>-<NÚMERO>`:
#
#   RED  Restrições de Dependência — limites de dependência e
#        relacionamento entre os componentes da arquitetura;
#   ROF  Restrições de Organização Estrutural e Fluxo HTTP — a
#        organização dos componentes, a estrutura dos módulos e o
#        fluxo das requisições e respostas HTTP;
#   SEG  Segurança e Tratamento de Dados — segurança da aplicação
#        e proteção/tratamento dos dados.
#
# O NÚMERO é SEQUENCIAL DENTRO DA CATEGORIA: cada prefixo
# reinicia em SOLAR-RED-001. O par categoria + número identifica a regra.
DEPENDENCY = "RED"
STRUCTURE = "ROF"
SECURITY = "SEG"

# Prefixo do produto, comum a todos os códigos.
CODE_PREFIX = "SOLAR"


def rule_code(category: str, number: int) -> str:
    """
    Monta o código de uma regra a partir da categoria e do número.

    Exemplos:

        rule_code(DEPENDENCY, 1)  → "SOLAR-RED-001"
        rule_code(STRUCTURE, 4)   → "SOLAR-ROF-004"
        rule_code(SECURITY, 8)    → "SOLAR-SEG-008"
    """

    return f"{CODE_PREFIX}-{category}-{number:03d}"


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