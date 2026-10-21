# Contexto da SOLAR-SEG-002: os campos que um Resource expõe.
#
# `frozen` porque é o retrato do que o scanner leu — a regra compara,
# não altera.
from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceExposure:
    """
    Descreve os CAMPOS EXPOSTOS por um Resource.

    O ResourceExposureScanner produz esta estrutura a partir das
    chaves de texto usadas no corpo da classe:

        class UserResource(Resource):
            @classmethod
            def to_object(cls, data):
                return {
                    "id": data["id"],
                    "password": data["password"],
                }

        resource = "UserResource"
        fields   = {"id", "password"}

    O scanner NÃO decide se há violação: isso é responsabilidade
    da Rule SOLAR-SEG-002.

    resource:
        Nome da classe Resource.

    fields:
        Chaves de texto expostas pelo Resource.

    file / line:
        Local da declaração da classe.
    """

    resource: str

    # `frozenset` e não `list`: a pergunta é "o campo X está
    # exposto?" — pertinência, não ordem. Assim a comparação com a
    # lista de campos proibidos não depende de como o código foi
    # escrito.
    fields: frozenset[str]

    file: str
    line: int
