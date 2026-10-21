# Contrato de sanitização: o que chegou pode ser normalizado antes
# de virar dado da aplicação?
#
# Segundo passo do RequestPipeline. O que ele NÃO faz:
#
#     - não confere presença de campo obrigatório (isso é do
#       Validator, que vem ANTES);
#     - não decide regra de negócio (isso é do UseCase/Domain).
#
# A implementação concreta depende do tipo de conteúdo e é injetada
# no HttpInput, que é lido pela Atmosphere.
from abc import ABC, abstractmethod


class Sanitizer(ABC):
    """
    Contrato de sanitização da SOLAR.

    Um Sanitizer normaliza e limpa os DADOS EXTERNOS recebidos
    antes que eles sejam validados e processados pela aplicação.

    A sanitização acontece DEPOIS da validação, e a ordem não é
    detalhe: o Validator confere que os campos obrigatórios
    CHEGARAM; o Sanitizer transforma o que chegou. Invertendo, um
    campo ausente quebraria no meio da limpeza, antes de alguém
    ter podido dizer que ele faltou.

    Toda entrada HTTP que transporta dados externos deve passar
    por um Sanitizer (SOLAR-ROF-001).

    O Sanitizer é específico ao TIPO DE CONTEÚDO recebido:

        application/json                  → JsonSanitizer
        multipart/form-data               → FileSanitizer
        application/x-www-form-urlencoded → FormSanitizer

    Por isso o contrato NÃO fixa o formato do payload: cada
    Sanitizer define o formato que trata.

    A implementação concreta é injetada no HttpInput
    (injeção de dependência) e aplicada pela Atmosphere
    através do RequestPipeline.
    """

    # `payload` sem tipo anotado: o formato é decisão de cada
    # Sanitizer (dict do JSON, `FileStorage` do multipart, ...). O
    # contrato é o mesmo para todos.
    @abstractmethod
    def sanitize(self, payload):
        """
        Sanitiza o payload recebido e retorna a versão
        normalizada.

        O formato do payload depende do tipo de conteúdo
        (JSON, form data, arquivos, ...).
        """
        raise NotImplementedError
