# Contexto da SOLAR-ROF-003: a fronteira de uma responsabilidade.
#
# "Contrato" aqui é o que a responsabilidade RECEBE e DEVOLVE — não
# assinatura eletrônica. Mesmo nome, assunto diferente, e o
# docstring da classe insiste nisso porque a confusão é comum.
from dataclasses import dataclass


@dataclass(frozen=True)
class ResponsibilityContract:
    """
    Descreve os contratos de entrada e saída de uma
    responsabilidade (Controller ou UseCase).

    NOTA SOBRE O NOME: este contrato NÃO tem relação com
    "assinatura" eletrônica/digital (assinatura de documentos,
    certificados, tokens). Aqui "contrato" significa o que a
    responsabilidade RECEBE e DEVOLVE.

    owner:
        Identificação da responsabilidade
        (ex.: "UserController.store", "CreateUserUseCase.execute").

    input_type:
        Tipo que representa a ENTRADA da responsabilidade.

    output_type:
        Tipo que representa a SAÍDA da responsabilidade.

    Os tipos devem ser contratos NOMEADOS (Input, Output, Entity,
    Resource). Estruturas anônimas (dict, list, tuple, set) como
    contrato violam a SOLAR-ROF-003.

    Importante: descreve apenas a FRONTEIRA da responsabilidade.
    Coleções anônimas usadas no processamento interno (iteração,
    agregação, transformação) não fazem parte do contrato e não
    violam a regra.

    A validação é responsabilidade da Rule SOLAR-ROF-003.
    """

    owner: str

    # `type | str`: instância de tipo em tempo de execução, NOME em
    # análise estática — mesma razão do HttpInput. `None` é
    # permitido porque uma responsabilidade pode não receber (ou
    # não devolver) nada, e a regra trata esse caso à parte.
    input_type: type | str | None = None
    output_type: type | str | None = None
