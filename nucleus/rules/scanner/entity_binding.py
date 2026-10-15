# Contexto da SOLAR-ARCH-029: dados de entrada indo direto para um
# contrato nomeado.
#
# O que a regra persegue é a ATRIBUIÇÃO EM MASSA: o campo que o
# cliente não deveria poder escolher (`is_admin`, `role`) entra no
# objeto só porque veio no corpo da requisição.
from dataclasses import dataclass


@dataclass(frozen=True)
class EntityBinding:
    """
    Representa dados de ENTRADA sendo despejados direto em um
    contrato nomeado (Entity/Model/Input).

    target:
        Nome de quem RECEBE os dados (ex.: "DocumentEntity",
        "DocumentModel", "Model.query").

    source:
        De onde os dados vêm, normalizado:

            "{}"                 dict literal (campos explícitos)
            "request.json"       cru da requisição
            "payload"            variável
            "DocumentInput"      contrato nomeado

    kind:
        Como os dados entram:

            "expansion"  DocumentEntity(**request.json)
            "update"     Model.query.update(**payload)
            "mapping"    DocumentEntity.from_dict(request.json)
            "setattr"    for k, v in payload.items():
                             setattr(entity, k, v)

    O scanner DESCREVE; quem decide a política é a Rule
    SOLAR-ARCH-029.
    """

    target: str
    source: str

    # `kind` é a FORMA da ligação (expansion / update / mapping /
    # setattr). A regra acusa todas, mas a mensagem cita a forma
    # porque a correção é diferente em cada uma.
    kind: str

    file: str
    line: int
