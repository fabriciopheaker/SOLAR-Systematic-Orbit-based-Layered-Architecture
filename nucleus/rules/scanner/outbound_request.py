# Contexto da SOLAR-SEG-010: uma chamada para serviço externo.
#
# O scanner descreve quem COMPÕE a URL (`names`), e a regra decide se
# esses nomes são confiáveis. A decisão fica na regra porque
# "confiável" é política: `BASE_URL` vem do ambiente e é confiável;
# `host` vem da requisição e não é.
from dataclasses import dataclass


@dataclass(frozen=True)
class OutboundRequest:
    """
    Representa uma chamada da aplicação para um serviço EXTERNO.

    package:
        Biblioteca usada (ex.: "requests", "httpx").

    url:
        A expressão da URL, como está escrita no código.

    names:
        Identificadores que compõem a URL. É por eles que se
        decide se a URL é CONFIÁVEL:

            "https://api.exemplo.com/users"   → ()            constante
            f"{BASE_URL}/users"               → ("BASE_URL",)  constante
            f"http://{host}/callback"         → ("host",)      entrada
            request.args["next"]              → ("request", "args")

    O scanner DESCREVE (quais identificadores compõem a URL);
    quem decide a política é a Rule SOLAR-SEG-010.
    """

    package: str
    url: str

    # `frozenset` de NOMES, e não a URL pronta: a URL é texto
    # montado em tempo de execução, e a única coisa verificável
    # estaticamente é de onde vêm os pedaços.
    names: frozenset[str]

    file: str
    line: int
