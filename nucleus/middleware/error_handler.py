# Resposta de erro segura + gancho para observadores.
#
# É a peça que fecha a SOLAR-SEG-008 pelo lado da aplicação: o detalhe
# interno vai para o log (via `detail`) e o cliente recebe código,
# mensagem genérica e referência.
#
# O gancho `observers` é o único ponto de contato com o Observatório — e
# o contato é INVERTIDO: o Nucleus não importa `observatory`; o
# Observatório se pluga aqui. A direção da dependência é
# Observatory -> Nucleus.
import secrets
from collections.abc import Mapping


class ErrorHandler:
    """
    Monta a resposta de erro SEGURA e separa o que NÃO pode sair
    da aplicação.

    O problema que isto resolve (SOLAR-SEG-008): a resposta para
    quem chamou precisa dizer O QUE deu errado, não COMO a
    aplicação é feita por dentro.

        except Exception as error:
            logger.exception("falha ao processar")   ← detalhe aqui
            return ErrorHandler().handle(error)      ← resposta aqui

    `handle()` devolve apenas:

        {
            "code":      "INVALID_UPLOAD" | "INTERNAL_ERROR",
            "message":   mensagem GENÉRICA,
            "reference": identificador do ocorrido,
        }

    A `reference` é o que liga a resposta ao log: quem reporta o
    problema informa o código, e o time encontra o detalhe no
    servidor — sem que o detalhe tenha saído de lá.

    `detail()` monta o texto do LOG (aqui o detalhe interno é
    bem-vindo).

    O gancho `observers` é por onde o Observatório se pluga:
    cada observador é chamado com (erro, payload, contexto) e
    recebe tudo o que precisa para registrar. O Nucleus NÃO
    conhece o Observatório — a direção da dependência é
    Observatory → Nucleus.

    `expose_details=True` existe para o desenvolvimento local.
    Em produção isso é exatamente o vazamento que a regra proíbe.
    """

    # A mensagem é CONSTANTE, e não montada com dado do erro: qualquer
    # informação variável aqui seria o começo do vazamento.
    GENERIC_MESSAGE = "Não foi possível processar a solicitação."

    # Código usado quando a exceção não traz o seu.
    INTERNAL_CODE = "INTERNAL_ERROR"

    # Nome do atributo gravado NA EXCEÇÃO. O `solar_` na frente evita
    # colidir com atributo de exceção de biblioteca.
    REFERENCE_ATTRIBUTE = "solar_reference"

    def __init__(
        self,
        expose_details: bool = False,
        identify=None,
        observers=None
    ):
        self.expose_details = expose_details

        # Gerador de referência INJETÁVEL: o teste usa um previsível para
        # poder afirmar o conteúdo do payload.
        self._identify = identify or self._random_reference

        # Tupla e não lista: os observadores não mudam por acidente no
        # meio de uma requisição — quem liga mais um usa `observe()`.
        self.observers = tuple(observers or ())

    def observe(self, *observers) -> None:
        """
        Liga observadores ao handler.

        Cada observador é um callable (erro, payload, contexto). O
        Nucleus não conhece o Observatório: conhece este gancho.
        """

        self.observers = (*self.observers, *observers)

    # `secrets` e não `random`: a referência é lida por quem reporta o
    # problema e procurada no log — previsível, ela poderia ser
    # adivinhada para consultar o registro de outra pessoa.
    @staticmethod
    def _random_reference() -> str:
        return secrets.token_hex(6)

    def handle(
        self,
        error: BaseException,
        context: Mapping | None = None
    ) -> dict:
        """
        Payload SEGURO para quem chamou.

        Antes de devolver, avisa os observadores ligados — é por
        aqui que o Observatório recebe o erro, sem que o Nucleus
        precise conhecê-lo.
        """

        # Três campos, e NENHUM deles é o texto da exceção: o payload é o
        # contrato com quem chamou.
        payload = {
            "code": self.code(error),
            "message": self.message(error),
            "reference": self.reference(error),
        }

        # Avisa DEPOIS de montar o payload: o observador recebe o que foi
        # RESPONDIDO, e é essa ligação que permite achar o detalhe no log
        # a partir do que o cliente reportou.
        self._notify(error, payload, context)

        return payload

    def _notify(
        self,
        error: BaseException,
        payload: Mapping,
        context: Mapping | None
    ) -> None:
        """
        Avisa cada observador ligado ao handler.

        Observar é BEST-EFFORT: a falha de um observador não pode
        mudar a resposta de quem já recebeu um erro.
        """

        for observer in self.observers:

            # `context or {}` para o observador não precisar tratar
            # `None`.
            try:
                observer(error, payload, context or {})

            # `except Exception: continue` é BEST-EFFORT deliberado: quem
            # já recebeu um erro não pode receber um segundo porque o
            # registrador falhou. O Observatório grava em SQLite, e o
            # banco pode estar indisponível.
            except Exception:
                continue

    def code(self, error: BaseException) -> str:
        """
        Código do erro quando a exceção traz um; senão, genérico.
        """

        # `getattr` com padrão: nem toda exceção tem `code`. E o `or`
        # cobre o `code` VAZIO, que também não serve como resposta.
        return getattr(error, "code", None) or self.INTERNAL_CODE

    def message(self, error: BaseException) -> str:
        """
        Mensagem para quem chamou.

        Sempre genérica — exceto em desenvolvimento, quando
        `expose_details` foi ligado de propósito.
        """

        # O caminho NORMAL: mensagem fixa, sem nada do erro.
        if not self.expose_details:
            return self.GENERIC_MESSAGE

        # Só com `expose_details` ligado, que é para desenvolvimento
        # local. Em produção isto é exatamente o vazamento que a regra
        # proíbe.
        return (
            f"{self.GENERIC_MESSAGE} "
            f"({type(error).__name__}: {error})"
        )

    def reference(self, error: BaseException) -> str:
        """
        Identificador estável do ocorrido.

        Fica guardado na PRÓPRIA exceção, para que `handle()` e
        `detail()` produzam sempre a mesma referência.
        """

        # Já existe? Devolve a MESMA: `handle()` e `detail()` precisam
        # produzir a mesma referência, senão a busca no log não acha
        # nada.
        reference = getattr(error, self.REFERENCE_ATTRIBUTE, None)

        if reference is not None:
            return reference

        reference = self._identify()

        # Grava na PRÓPRIA exceção — é o que faz a segunda chamada cair
        # no `if` acima.
        try:
            setattr(error, self.REFERENCE_ATTRIBUTE, reference)
        except AttributeError:
            # Exceções com __slots__ não aceitam atributo novo; a
            # referência continua válida, só não fica guardada.
            pass

        return reference

    def detail(self, error: BaseException) -> str:
        """
        Texto para o LOG do servidor.
        """

        # Aqui o detalhe interno é BEM-VINDO: este texto vai para o log do
        # servidor, e é ele que dá sentido à referência. A referência vem
        # entre colchetes para ser fácil de procurar no log.
        return (
            f"[{self.reference(error)}] "
            f"{type(error).__name__}: {error}"
        )
