from nucleus.exceptions.contract_exception import ContractException
from nucleus.rules.rule_engine import RuleEngine
from nucleus.rules.architecture.http_input_must_pass_through_sanitization_and_validation import (
    HttpInputMustPassThroughSanitizationAndValidation
)
from nucleus.contracts.http_input import HttpInput
from nucleus.contracts.sanitizer import Sanitizer
from nucleus.contracts.validator import Validator


class RequestPipeline:
    """
    Mecanismo (middleware) do Nucleus que garante que toda
    entrada HTTP que transporta dados externos passe por
    validação e sanitização antes de alcançar o Planet.

    A Atmosphere injeta o Sanitizer e o Validator apropriados ao
    tipo de conteúdo em cada HttpInput (injeção de dependência).
    O pipeline apenas aplica a regra SOLAR-ARCH-013 e executa as
    etapas na ordem correta:

        HTTP Input → Validator → Sanitizer → Planet

    A ordem NÃO é detalhe. A validação confere se os campos
    esperados EXISTEM; a sanitização limpa os valores. Invertendo
    isso, o Sanitizer tentaria limpar campo que pode não ter
    chegado — e quebraria antes de a validação poder dizer o que
    faltou.

    Entradas que NÃO transportam dados externos passam direto,
    sem validação ou sanitização.
    """

    def __init__(self) -> None:

        # Um motor com UMA regra: o contexto do pipeline é o HttpInput, e
        # misturar regras de outro contexto aqui quebraria a execução.
        self._engine = RuleEngine([
            HttpInputMustPassThroughSanitizationAndValidation()
        ])

    def handle(
        self,
        http_input: HttpInput,
        payload
    ):
        """
        Processa o payload de uma entrada HTTP.

        Quando a entrada transporta dados externos:
            1. Aplica a regra SOLAR-ARCH-013;
            2. Valida o payload (os campos esperados existem?);
            3. Sanitiza o payload já validado;
            4. Retorna o payload sanitizado.

        Caso contrário, retorna o payload original.
        """

        # Entrada sem dados externos passa direto — é o caso do
        # `/solar/health`: não há o que validar nem o que limpar.
        if not http_input.transports_data():
            return payload

        # Garante o contrato da SOLAR-ARCH-013.
        self._engine.validate(http_input)

        # Os dois resolvidos antes de usar, e resolvidos com `isinstance`
        # (ver `_validator`/`_sanitizer`): na análise estática o campo pode
        # ser o NOME da classe, e aqui não dá para chamar método de string.
        validator = self._validator(http_input)
        sanitizer = self._sanitizer(http_input)

        # VALIDAR e só então SANITIZAR — a ordem é a razão de existir
        # deste método (ver o docstring da classe).
        validator.validate(payload)

        # Retorna o resultado do Sanitizer, e não o payload: o que segue
        # para o Planet é o dado já normalizado.
        return sanitizer.sanitize(payload)

    def _sanitizer(self, http_input: HttpInput) -> Sanitizer:
        """
        O pipeline roda em TEMPO DE EXECUÇÃO: exige a
        implementação real, não o nome declarado usado na
        validação estática.
        """

        # `isinstance` e não `is None`: uma STRING aqui (o nome que a
        # análise estática encontrou) passaria pela checagem de ausência
        # e quebraria depois, com erro obscuro. O `isinstance` recusa as
        # duas coisas de uma vez, com código de contrato.
        if not isinstance(http_input.sanitizer, Sanitizer):
            raise ContractException(
                "O Sanitizer fornecido não implementa o contrato "
                "Sanitizer.",
                code="INVALID_SANITIZER"
            )

        return http_input.sanitizer

    def _validator(self, http_input: HttpInput) -> Validator:
        """
        O pipeline roda em TEMPO DE EXECUÇÃO: exige a
        implementação real, não o nome declarado usado na
        validação estática.
        """

        # Mesmo cuidado do `_sanitizer`, e a mesma mensagem trocada:
        # validar o contrato ERRADO daria um diagnóstico enganoso.
        if not isinstance(http_input.validator, Validator):
            raise ContractException(
                "O Validator fornecido não implementa o contrato "
                "Validator.",
                code="INVALID_VALIDATOR"
            )

        return http_input.validator
