# Contexto da SOLAR-SEG-008: o uso de um detalhe interno de erro.
#
# O scanner descreve DUAS coisas independentes — o QUE apareceu
# (`detail`) e para ONDE foi (`destination`) — porque é a combinação
# das duas que decide a violação: `str(error)` no log é correto,
# `str(error)` na resposta é vazamento.
from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorExposure:
    """
    Representa o uso de um DETALHE INTERNO de um erro no
    tratamento de exceção.

    handler:
        Nome da variável da exceção (ex.: "error" em
        `except Exception as error:`).

    detail:
        Como o detalhe interno aparece:

            "str"        str(error)
            "repr"       repr(error)
            "format"     "{}".format(error)
            "f-string"   f"falhou: {error}"
            "args"       error.args
            "traceback"  traceback.format_exc()

    destination:
        Para ONDE o detalhe vai:

            "response"   sai do handler (return, raise ou resposta
                         montada) — é um VAZAMENTO;
            "log"        vai para o log do servidor — correto;
            "local"      não foi possível provar que sai (ex.: virou
                         registro de relatório) — não é acusado, mas
                         também não é uma garantia.

    O scanner DESCREVE; quem decide a política é a Rule
    SOLAR-SEG-008.
    """

    handler: str
    detail: str

    # `response` é o único destino acusável. `log` é o destino
    # correto e `local` é o caso em que o scanner não conseguiu
    # provar que o detalhe sai — registrar `local` explicitamente,
    # em vez de tratar como `response`, é o que evita o falso
    # positivo.
    destination: str

    file: str
    line: int
