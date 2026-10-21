# SOLAR-ROF-001 — toda entrada que transporta dados externos passa
# por Validator e Sanitizer.
#
# A regra lê o `HttpInput` que o `http_input_scanner` produziu a partir
# das rotas. O critério é TRANSPORTE DE DADOS (`transports_data()`), e
# não o verbo HTTP: é isso que faz uma rota nova (verbo novo, tipo de
# conteúdo novo) já nascer coberta, sem alterar a regra.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import STRUCTURE, Rule, rule_code
from nucleus.contracts.http_input import HttpInput


class HttpInputMustPassThroughSanitizationAndValidation(Rule):
    """
    Regra arquitetural:

    SOLAR-ROF-001

    Toda entrada HTTP que TRANSPORTA DADOS EXTERNOS deve passar
    pelo pipeline de Sanitization e Validation apropriado ao tipo
    de conteúdo recebido.

    Fluxo exigido:

        HTTP Input → Validator → Sanitizer → Planet

    A ordem importa: a validação confere se os campos esperados
    EXISTEM, e só depois o Sanitizer limpa os valores. Sanitizar
    primeiro seria limpar campo que pode não ter chegado.

    O critério é o TRANSPORTE DE DADOS EXTERNOS, não o verbo HTTP.
    Portanto a regra NÃO é "POST exige validação":

        POST  /documents  multipart/form-data  → exige pipeline
        POST  /users      application/json     → exige pipeline
        PUT   /users      application/json     → exige pipeline
        PATCH /users      application/json     → exige pipeline
        POST  /users      form-urlencoded      → exige pipeline
        GET   /solar/health  (sem corpo)       → NÃO exige

    O Sanitizer e o Validator são específicos ao tipo de conteúdo
    (JsonSanitizer/JsonValidator, FileSanitizer/FileValidator,
    FormSanitizer/FormValidator, ...). A regra exige que EXISTAM;
    qual implementação é apropriada é decisão do contrato.

    ESCOPO — o que esta regra NÃO cobre:

    A regra NÃO valida regra de negócio. Validações estruturais
    de entrada (arquivo enviado, tamanho, extensão, MIME type,
    quantidade, arquivo vazio) pertencem ao Validator.

    Regras de negócio ("o documento precisa representar um
    contrato válido com determinado número de contrato") ficam no
    UseCase/Domain e NÃO devem ser transferidas ao Validator para
    satisfazer esta regra.

    Exemplo válido:

        HttpInput(
            method="POST",
            name="/documents",
            sanitizer=FileSanitizer(),
            validator=FileValidator(),
        )

    O contexto desta regra é um HttpInput — diferente do contexto
    das regras de Dependency (SOLAR-RED-001 a SOLAR-RED-012).
    """

    def code(self) -> str:
        return rule_code(STRUCTURE, 1)

    def description(self) -> str:
        return (
            "Toda entrada HTTP que transporta dados externos deve "
            "passar por Sanitization e Validation apropriadas ao "
            "tipo de conteúdo recebido."
        )

    def validate(self, http_input: HttpInput) -> None:

        # A regra só se aplica a entradas que transportam
        # dados externos.
        if not http_input.transports_data():
            return

        # Recolhe TUDO o que falta antes de acusar: a mensagem cita os
        # dois guardas de uma vez, e quem corrige não precisa rodar o
        # check duas vezes para descobrir o segundo.
        missing = self._missing_guards(http_input)

        if not missing:
            return

        raise SolarException(
            self._build_message(http_input, missing)
        )

    def _missing_guards(
        self,
        http_input: HttpInput
    ) -> list[str]:

        missing: list[str] = []

        # Checagem por AUSÊNCIA e não por presença: `str` (o nome
        # encontrado na análise estática) também satisfaz o contrato
        # — ver `HttpInput.sanitizer`. Só `None` acusa.
        if http_input.sanitizer is None:
            missing.append("Sanitizer")

        if http_input.validator is None:
            missing.append("Validator")

        return missing

    def _build_message(
        self,
        http_input: HttpInput,
        missing: list[str]
    ) -> str:

        return (
            f"{self.code()}: "
            f"a entrada HTTP '{http_input.method} "
            f"{http_input.name}' não possui "
            f"{' e '.join(missing)}. "
            f"Toda entrada HTTP que transporta dados externos deve "
            f"passar por Sanitizer e Validator apropriados ao tipo "
            f"de conteúdo."
        )
