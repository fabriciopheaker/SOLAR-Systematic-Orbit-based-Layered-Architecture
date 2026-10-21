# Contexto da SOLAR-ROF-001: a entrada HTTP de uma rota.
#
# É o contrato que o scanner ESTÁTICO produz e que o RequestPipeline
# CONSOME em tempo de execução — por isso os campos aceitam tanto a
# instância quanto o nome da implementação.
from dataclasses import dataclass

from nucleus.contracts.sanitizer import Sanitizer
from nucleus.contracts.validator import Validator


@dataclass(frozen=True)
class HttpInput:
    """
    Representa uma ENTRADA HTTP da aplicação.

    method:
        Verbo HTTP (ex.: "POST", "PUT", "PATCH").

    name:
        Identificação da entrada (ex.: "/documents").

    content_type:
        Tipo do conteúdo recebido (ex.: "application/json",
        "multipart/form-data", "application/x-www-form-urlencoded").
        None quando o tipo de conteúdo não é declarado.

    sanitizer / validator:
        Sanitizer e Validator apropriados ao tipo de conteúdo.

        Em tempo de execução são INSTÂNCIAS, declaradas na ROTA
        (`sanitizer=CreateUserSanitizer`). Na validação ESTÁTICA o
        scanner encontra apenas o NOME da implementação declarada ali
        (ex.: "FileSanitizer") — por isso o contrato aceita
        `Sanitizer | str | None`.

    carries_data:
        Se a entrada transporta dados externos.

            True  → transporta
            False → não transporta
            None  → derivar do content_type (declarado ⇒ transporta)

        O scanner estático informa explicitamente True para rotas
        cujo MÉTODO aceita corpo (POST/PUT/PATCH), mesmo sem
        content_type declarado — assim um dev não escapa da
        SOLAR-ROF-001 omitindo o tipo de conteúdo.

    Esta abstração representa ENTRADA HTTP, e não "POST": o que a
    torna relevante para a SOLAR-ROF-001 é o fato de TRANSPORTAR
    DADOS EXTERNOS, e não o verbo utilizado.
    """

    method: str
    name: str
    content_type: str | None = None
    # `Sanitizer | str`: INSTÂNCIA em tempo de execução, NOME em
    # análise estática. O mesmo contrato serve aos dois momentos
    # porque o scanner só enxerga o texto do código, e o
    # `SolarBlueprint` só lida com objetos.
    sanitizer: Sanitizer | str | None = None
    validator: Validator | str | None = None

    # `None` significa "não foi dito", e é diferente de `False`.
    # Vazio por padrão para que o scanner possa afirmar True sem
    # depender de `content_type`.
    carries_data: bool | None = None

    def transports_data(self) -> bool:
        """
        Resposta resolvida: a entrada transporta dados externos?

        Prioriza a informação EXPLÍCITA (`carries_data`); quando
        ausente, deriva do tipo de conteúdo declarado.

        O critério NÃO é o verbo HTTP:

            GET   /solar/health                  → não transporta
            POST  /documents  (multipart)        → transporta
            PUT   /users      (application/json) → transporta
            PATCH /users      (application/json) → transporta

        Assim, novos tipos de entrada não exigem exceções na
        arquitetura: basta declarar o tipo de conteúdo.
        """

        # `is not None` e não `if self.carries_data`: `False` é uma
        # resposta e tem que ser respeitada. Só a AUSÊNCIA de
        # resposta autoriza derivar do tipo de conteúdo.
        if self.carries_data is not None:
            return self.carries_data

        # Declarar o tipo de conteúdo já é declarar que vêm dados no
        # corpo.
        return self.content_type is not None
