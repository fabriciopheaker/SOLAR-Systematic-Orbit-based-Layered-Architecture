# SOLAR-ARCH-028 — erro não vaza o interior da aplicação.
#
# A contrapartida é o Observatório: o detalhe PRECISA ser registrado,
# só que no log. Por isso a regra olha o DESTINO do detalhe, e não a
# presença dele — ver o docstring da classe.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import Rule
from nucleus.rules.scanner.error_exposure import ErrorExposure


class ErrorsMustNotLeakInternals(Rule):
    """
    Regra arquitetural:

    SOLAR-ARCH-028

    Erros NÃO podem vazar informações internas.

    Quando algo falha, a resposta para quem chamou deve dizer o
    QUE deu errado, e não COMO a aplicação é feita por dentro.

    É VIOLAÇÃO:

        except Exception as error:
            return {"error": str(error)}                    ❌
            return jsonify({"erro": f"{error}"})            ❌
            raise ValueError(f"falhou: {error}")            ❌
            return {"traceback": traceback.format_exc()}    ❌
            return {"erro": error.args}                     ❌

    Correto:

        except Exception as error:
            logger.exception("falha ao processar o documento")
            return ErrorHandler().handle(error)             ✅

    O detalhe interno (mensagem da exceção, traceback, caminho,
    nome de tabela/coluna) é informação de RECONHECIMENTO:
    revela estrutura, tecnologia e pontos de falha para quem
    estiver sondando a aplicação.

    O detalhe continua sendo registrado — mas no LOG, que é do
    servidor. Por isso o scanner distingue o DESTINO, e só o
    destino "response" é violação:

        response   demonstrouvelmente sai do handler (return,
                   raise ou resposta montada que CONTÉM o detalhe);
        log        vai para uma chamada de log;
        local      não foi possível provar que sai — não é acusado,
                   mas também não é garantia.

    Passar perto de um `return` não basta: o detalhe tem que
    estar no valor retornado. Sem isso, guardar a mensagem em um
    registro de relatório seria acusado — quando o detalhe virou
    registro, não resposta.

    Instrumento: `nucleus.middleware.error_handler.ErrorHandler`
    monta a resposta segura e separa o que vai para o log.

    O contexto desta regra é um ErrorExposure.
    """

    # Destino que caracteriza violação. Os outros dois valores
    # possíveis — "log" (correto) e "local" (não comprovado) — não
    # acusam. É constante para o nome do destino aparecer uma vez só
    # no código.
    EXPOSED_DESTINATION = "response"

    def code(self) -> str:
        return "SOLAR-ARCH-028"

    def description(self) -> str:
        return "Erros não podem vazar informações internas."

    def validate(self, exposure: ErrorExposure) -> None:

        # Só o destino `response` acusa. `log` é o comportamento
        # correto e `local` é o caso em que o scanner não conseguiu
        # provar que o detalhe sai — acusá-lo daria falso positivo.
        if exposure.destination != self.EXPOSED_DESTINATION:
            return

        raise SolarException(
            self._build_message(exposure)
        )

    def _build_message(self, exposure: ErrorExposure) -> str:

        # `exposure.detail` é a FORMA do detalhe ("str", "f-string",
        # "traceback"), nunca o conteúdo: a mensagem não pode ser ela
        # própria um vazamento — o relatório circula.
        return (
            f"{self.code()}: o detalhe interno '{exposure.detail}' "
            f"da exceção '{exposure.handler}' é enviado na resposta "
            f"em {exposure.file}:{exposure.line}. "
            f"Responda com código e mensagem genérica e registre o "
            f"detalhe no log do servidor."
        )
