# Contexto do scanner de arquitetura: uma ARESTA do grafo de
# dependências (`source` importa `target`).
#
# É a estrutura mais reaproveitada do projeto — onze regras da
# SOLAR-ARCH leem esta mesma aresta, e cada uma olha uma direção
# proibida diferente. Por isso o contexto é a aresta crua, sem
# nenhum julgamento embutido.
from dataclasses import dataclass


@dataclass(frozen=True)
class Dependency:
    """
    Representa uma dependência encontrada no código-fonte.

    source:
        Módulo que possui o import.

    target:
        Módulo importado.

    file:
        Arquivo onde a dependência foi encontrada.

    line:
        Linha onde o import foi declarado.
    """

    # Ambos são caminhos PONTUADOS de módulo
    # (ex.: "orbits.database.models.user_model"), e não caminhos de
    # arquivo: é o módulo que diz a qual camada a peça pertence.
    source: str
    target: str

    file: str
    line: int