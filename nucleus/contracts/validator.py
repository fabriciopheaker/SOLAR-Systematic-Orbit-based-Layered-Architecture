# Contrato de validação: a entrada atende ao que a aplicação
# espera receber?
#
# Primeiro passo do RequestPipeline. O que ele NÃO faz:
#
#     - não limpa dado (isso é do Sanitizer, que vem depois);
#     - não decide regra de negócio (isso é do UseCase/Domain).
#
# A implementação concreta depende do tipo de conteúdo e é
# injetada no HttpInput, que é lido pela Atmosphere.
from abc import ABC, abstractmethod


class Validator(ABC):
    """
    Contrato de validação da SOLAR.

    Um Validator verifica se os DADOS EXTERNOS recebidos atendem
    às regras ESTRUTURAIS da entrada.

    A validação acontece ANTES da sanitização. A ordem importa:
    sanitizar é transformar o que chegou, e não há o que
    transformar no campo que não foi enviado. Conferir a presença
    primeiro é o que permite os dois passos viverem separados.

    Toda entrada HTTP que transporta dados externos deve passar
    por um Validator (SOLAR-ROF-001).

    O Validator é específico ao TIPO DE CONTEÚDO recebido:

        application/json                  → JsonValidator
        multipart/form-data               → FileValidator
        application/x-www-form-urlencoded → FormValidator

    ESCOPO: o Validator cuida da ENTRADA (arquivo enviado,
    tamanho, extensão, MIME type, quantidade, arquivo vazio,
    campos obrigatórios). Regras de NEGÓCIO permanecem no
    UseCase/Domain e não devem ser transferidas para cá.

    A implementação concreta é injetada no HttpInput
    (injeção de dependência) e aplicada pela Atmosphere
    através do RequestPipeline.
    """

    # `payload` sem tipo anotado de propósito: o formato depende
    # do tipo de conteúdo (dict do JSON, `FileStorage` do
    # multipart, ...) e o contrato é o mesmo para todos.
    @abstractmethod
    def validate(self, payload) -> None:
        """
        Valida o payload recebido.

        Deve lançar ValidationException quando o payload
        não atender às regras estruturais da entrada.

        O formato do payload depende do tipo de conteúdo
        (JSON, form data, arquivos, ...).
        """
        raise NotImplementedError
