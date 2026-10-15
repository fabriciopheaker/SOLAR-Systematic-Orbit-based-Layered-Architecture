# Contexto da SOLAR-ARCH-027: um uso de JWT/Token no código.
#
# Os campos anuláveis são o ponto: `None` significa "o scanner não
# conseguiu ver", e não "está errado" nem "está certo". A regra
# acusa só o que foi VISTO errado — acusar a dúvida daria falso
# positivo em token montado em tempo de execução.
from dataclasses import dataclass


@dataclass(frozen=True)
class TokenUsage:
    """
    Descreve um uso de JWT/Token encontrado no código-fonte.

    operation:
        "encode" (emissão) ou "decode" (leitura).

    algorithm:
        Algoritmo declarado, quando informado.
        None quando não foi declarado explicitamente.

    verifies_signature:
        Para "decode": False quando a verificação de assinatura
        foi desativada. None quando não há informação.

    has_expiration:
        Para "encode": False quando o payload não declara "exp".
        None quando o payload não é um literal (não verificável).

    file / line:
        Onde o uso aparece.
    """

    operation: str

    # Tri-estado nos três: `None` é "não verifiquei", `False` é
    # "verifiquei e está errado". A regra só acusa o `False`.
    algorithm: str | None
    verifies_signature: bool | None
    has_expiration: bool | None

    file: str
    line: int
