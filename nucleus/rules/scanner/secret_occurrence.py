# Contexto da SOLAR-SEG-004: a DESCRIÇÃO de um literal que casa
# com um padrão de segredo.
#
# Sem o valor: guardar o texto encontrado faria do relatório — e do
# arquivo de auditoria — um novo vazamento.
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretOccurrence:
    """
    Representa um SEGREDO encontrado no código-fonte pelo seu
    CONTEÚDO (não pelo nome da variável).

    O valor do segredo NÃO é armazenado: só o padrão que casou e
    o local. Assim o relatório não vira um novo vazamento.

    pattern:
        Nome do padrão detectado (ex.: "aws-access-key").

    file / line:
        Onde o segredo aparece.

    Os três campos abaixo são FATOS sobre o local encontrado — o
    scanner os descreve, mas NÃO decide se há violação. Quem
    decide a política é a Rule SOLAR-SEG-004:

    documentation:
        o literal é um bloco de documentação (docstring ou texto
        solto), não um valor que o programa usa.

    suppressed:
        o trecho está anotado com o marcador explícito de
        exceção ("solar:allow-secret").

    example:
        o valor é um exemplo/placeholder conhecido
        ("AKIAIOSFODNN7EXAMPLE", "...-fake-..."), não uma
        credencial real.
    """

    pattern: str
    file: str
    line: int

    # Os três abaixo são FATOS sobre o local, não o veredito. Todos
    # começam em `False` porque ausência de informação não pode
    # virar justificativa: o que não foi marcado é violação até que
    # a regra diga o contrário.
    documentation: bool = False
    suppressed: bool = False
    example: bool = False
