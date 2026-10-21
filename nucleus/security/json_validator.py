# Validador de corpo JSON.
#
# É a guarda de ENTRADA (SOLAR-ROF-001) e o PRIMEIRO passo do
# pipeline: confere que os campos obrigatórios CHEGARAM. O
# sanitizador roda depois, sobre dado que se sabe completo — não há
# o que limpar no campo que não veio.
#
# ESCOPO: estrutura, não negócio. Aqui se responde "o corpo tem os
# campos que a entrada exige?". "O e-mail tem formato válido?" é do
# UseCase, e "o usuário já existe?" é do banco.

from collections.abc import Mapping

from nucleus.contracts.validator import Validator
from nucleus.exceptions.validation_exception import ValidationException
from nucleus.notication.notification import Notification


class JsonValidator(Validator):
    """
    Confere os campos OBRIGATÓRIOS de um corpo JSON.

        JsonValidator(required=("name", "email"))

    Um campo obrigatório está faltando em três casos, e os três são a
    mesma coisa para quem consome o dado:

        - a chave não veio;
        - veio com `None`;
        - veio como texto vazio ou só de espaços.

    Separá-los daria três mensagens para o mesmo problema.

    Recolhe TODOS os campos que faltam antes de recusar: quem está
    corrigindo a chamada precisa da lista inteira, e não de uma
    tentativa por campo.

    É ESPECÍFICO do tipo de conteúdo `application/json`, como manda o
    contrato: form data e arquivo têm o seu.
    """

    INVALID_PAYLOAD = "INVALID_JSON_BODY"
    MISSING_FIELDS = "MISSING_FIELDS"

    def __init__(self, required=()):
        # Tupla, e não lista: a exigência não muda depois de criada.
        # Um validador que muda de regra no meio da requisição seria
        # imprevisível.
        self.required = tuple(required)

    def validate(self, payload) -> None:
        """
        Levanta `ValidationException` quando o corpo não serve.
        """

        if not isinstance(payload, Mapping):
            raise ValidationException(
                "O corpo da requisição deve ser um objeto JSON.",
                code=self.INVALID_PAYLOAD
            )

        # O Notification é o acumulador do projeto: ele existe
        # exatamente para relatar vários problemas de uma vez.
        notification = Notification()

        for field in self.required:

            if self._present(payload, field):
                continue

            notification.add(
                code=self.MISSING_FIELDS,
                message=f"O campo '{field}' é obrigatório.",
                field=field
            )

        if not notification.has_errors():
            return

        # UMA exceção com a lista. O `code` é estável (quem trata não
        # lê a mensagem), e a mensagem junta os problemas.
        #
        # O que sai para o cliente NÃO é esta mensagem: o
        # ErrorHandler responde com mensagem genérica e guarda o
        # detalhe no log (SOLAR-SEG-008).
        raise ValidationException(
            self._message(notification),
            code=self.MISSING_FIELDS
        )

    @staticmethod
    def _present(payload: Mapping, field: str) -> bool:
        """
        Indica se o campo veio COM valor.
        """

        value = payload.get(field)

        if value is None:
            return False

        # Texto só de espaço é o mesmo que vazio — e é o que se
        # escreve quando o formulário manda o campo em branco.
        if isinstance(value, str):
            return bool(value.strip())

        return True

    @staticmethod
    def _message(notification: Notification) -> str:
        """
        Junta os problemas em uma frase.
        """

        return " ".join(
            error["message"] for error in notification.all()
        )
