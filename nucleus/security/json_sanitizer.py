# Sanitizador de corpo JSON.
#
# É a guarda de ENTRADA (SOLAR-ARCH-013) que LIMPA: o
# `JsonValidator` confere o que existe, este normaliza o que
# chegou. A ordem é essa — conferir antes de limpar — e a razão
# está no contrato `Sanitizer`.
#
# Ele não julga nada: não decide se o e-mail é válido nem se o nome
# é aceitável. O que ele tira do dado é o que NÃO é dado — espaço em
# volta, valor nulo, chave sem conteúdo.

from collections.abc import Mapping

from nucleus.contracts.sanitizer import Sanitizer
from nucleus.exceptions.validation_exception import ValidationException


class JsonSanitizer(Sanitizer):
    """
    Normaliza um corpo JSON antes de ele virar dado da aplicação.

        {"name": "  Ana  ", "apelido": None}
            → {"name": "Ana"}

    O que faz:

        - recusa payload que não seja um objeto JSON;
        - tira espaço em volta de todo valor de TEXTO;
        - descarta a chave cujo valor é `None`.

    O que NÃO faz: conferir campo obrigatório (é do `JsonValidator`),
    converter tipo e decidir regra de negócio (é do UseCase).

    É ESPECÍFICO do tipo de conteúdo `application/json`, como manda o
    contrato: form data e arquivo têm o seu.
    """

    # Mesmo código do validador para o mesmo problema: o corpo não é
    # objeto JSON. Um código por guarda faria quem trata a resposta
    # ter que conhecer os dois.
    INVALID_PAYLOAD = "INVALID_JSON_BODY"

    def sanitize(self, payload) -> dict:
        """
        Devolve uma CÓPIA normalizada do corpo.
        """

        # `Mapping` e não `dict`: o corpo pode chegar como qualquer
        # mapeamento, e recusar isso seria recusar dado bom pelo tipo
        # da caixa em que ele veio.
        if not isinstance(payload, Mapping):

            raise ValidationException(
                "O corpo da requisição deve ser um objeto JSON.",
                code=self.INVALID_PAYLOAD
            )

        # Dicionário NOVO, e não `payload` alterado no lugar: quem
        # chamou ainda tem a referência do corpo recebido, e mudá-lo
        # por baixo seria surpresa.
        sanitized: dict = {}

        for key, value in payload.items():

            # Chave sem valor não vira campo. `None` é a ausência
            # escrita de outra forma, e deixá-la passar empurraria
            # para o UseCase um problema que é de entrada.
            if value is None:
                continue

            # `strip()` só em TEXTO: número e booleano não têm espaço
            # em volta, e chamar `strip` neles estouraria. Espaço em
            # texto, porém, é ruído de digitação — "  Ana  " e "Ana"
            # são o mesmo nome.
            if isinstance(value, str):
                sanitized[key] = value.strip()
                continue

            sanitized[key] = value

        return sanitized
