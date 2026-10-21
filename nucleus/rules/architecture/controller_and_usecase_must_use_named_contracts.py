# SOLAR-ROF-003 — contrato é OBJETO, não `dict` solto.
#
# Regra de FRONTEIRA: olha só o que o `ResponsibilityContract` declara
# (entrada/saída), nunca o corpo do método. Coleção anônima no meio do
# processamento — índice, acumulador, filtro — é permitida.
import re

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import STRUCTURE, Rule, rule_code
from nucleus.contracts.responsibility_contract import ResponsibilityContract


class ControllerAndUseCaseMustUseNamedContracts(Rule):
    """
    Regra arquitetural:

    SOLAR-ROF-003

    Controllers e UseCases não podem utilizar estruturas de dados
    anônimas como CONTRATOS de entrada ou de saída.

    O contrato — o que entra e o que sai da responsabilidade —
    deve ser um objeto NOMEADO E EXPLÍCITO, para que o consumidor
    saiba exatamente o que está recebendo.

    Permitido (contratos nomeados):

        class UserInput:
            ...

        class UserInput(dict):
            ...

        class UsersOutput(list):
            ...

    Herdar de `dict`/`list` NÃO torna o contrato anônimo: a
    arquitetura reconhece `UserInput` e `UsersOutput` como
    contratos nomeados.

    Proibido (estrutura anônima literal):

        def execute(input):
            return {
                "id": 10,
                "name": "Fabrício",
            }

    ESCOPO — o que esta regra NÃO cobre:

    Coleções anônimas são PERMITIDAS no processamento INTERNO dos
    UseCases e Controllers: iteração, agregação, transformação,
    filtros, acumuladores, indexação temporária, montagem de
    estruturas intermediárias etc.

    Um `for` sobre uma lista, um `dict` local usado para indexar
    dados ou um `set` para deduplicar NÃO violam a regra.

    A regra observa apenas a FRONTEIRA da responsabilidade — o
    contrato declarado no ResponsibilityContract — nunca o corpo do método.
    Estruturas anônimas deixa de ser violação quando substituem
    contratos arquiteturais (Input, Output, Entity, Resource).

    Exemplo inválido:

        ResponsibilityContract(
            owner="UserController.store",
            input_type=dict,
            output_type=UserOutput,      # nomeado ✅
        )

    Exemplo válido:

        ResponsibilityContract(
            owner="ListUsersUseCase.execute",
            input_type=ListUsersInput,
            output_type=ListUsersOutput,
        )
    """

    # Coleções anônimas: rejeitadas APENAS como built-ins literais
    # no contrato. Subclasses NOMEADAS são contratos válidos.
    ANONYMOUS_STRUCTURES = (
        dict,
        list,
        tuple,
        set,
        frozenset,
    )

    # Nomes equivalentes (anotações em texto, ex.: "dict").
    ANONYMOUS_NAMES = frozenset({
        "dict",
        "list",
        "tuple",
        "set",
        "frozenset",
    })

    # Extrai identificadores de uma anotação em texto.
    #
    # Regex e não `ast`: a anotação chega como STRING quando vem do
    # scanner, e também quando o contrato é montado fora do código
    # (fixture, configuração).
    NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

    def code(self) -> str:
        return rule_code(STRUCTURE, 3)

    def description(self) -> str:
        return (
            "Controllers e UseCases não podem utilizar estruturas "
            "de dados anônimas como contratos de entrada ou saída."
        )

    def validate(self, contract: ResponsibilityContract) -> None:

        # Acumula entrada E saída: as duas podem estar erradas ao mesmo
        # tempo, e a mensagem cita as duas de uma vez.
        offenses = self._offenses(contract)

        if not offenses:
            return

        raise SolarException(
            self._build_message(contract, offenses)
        )

    def _offenses(
        self,
        contract: ResponsibilityContract
    ) -> list[tuple[str, str]]:
        """
        Verifica apenas os CONTRATOS declarados
        (entrada e saída). O corpo da responsabilidade
        não é analisado.
        """

        offenses: list[tuple[str, str]] = []

        # `(rótulo, valor)` e não só o valor: a mensagem precisa dizer
        # se o problema é a ENTRADA ou a SAÍDA — a correção acontece em
        # lugares diferentes.
        for label, value in (
            ("entrada", contract.input_type),
            ("saída", contract.output_type),
        ):

            if self._is_anonymous(value):
                offenses.append((label, str(value)))

        return offenses

    def _is_anonymous(self, value) -> bool:
        """
        Uma estrutura só é anônima quando o PRÓPRIO contrato é uma
        coleção built-in literal.

        Classes NOMEADAS — mesmo herdando de dict/list/set — são
        contratos válidos.
        """

        # `None` = contrato não declarado. Não é estrutura anônima:
        # pode ser uma responsabilidade que simplesmente não recebe
        # (ou não devolve) nada.
        if value is None:
            return False

        # Dois caminhos, porque o contrato aceita as duas formas
        # (`type | str | None`): o tipo de verdade, em tempo de
        # execução; e a anotação em texto, na análise estática.
        if isinstance(value, type):
            # IDENTIDADE, e não `issubclass`: só os built-ins literais
            # são anônimos. `class UserInput(dict)` é um contrato
            # NOMEADO e passa.
            return value in self.ANONYMOUS_STRUCTURES

        # Extrai os identificadores do texto e olha um a um:
        # `typing.Optional[dict]` e `dict[str, int]` têm o `dict` no
        # meio, e é isso que precisa ser pego.
        names = self.NAME_PATTERN.findall(str(value))

        # QUALQUER identificador anônimo condena a anotação: um
        # contrato que menciona `dict` em algum nível não é nomeado por
        # inteiro.
        return any(
            name.lower() in self.ANONYMOUS_NAMES
            for name in names
        )

    def _build_message(
        self,
        contract: ResponsibilityContract,
        offenses: list[tuple[str, str]]
    ) -> str:

        details = "; ".join(
            f"{label} = {value}"
            for label, value in offenses
        )

        return (
            f"{self.code()}: "
            f"O contrato da responsabilidade '{contract.owner}' "
            f"utiliza estrutura anônima ({details}). "
            f"Contratos de entrada e saída devem ser objetos "
            f"nomeados e explícitos (Input, Output, Entity, Resource) — "
            f"inclusive subclasses nomeadas de coleções. "
            f"Coleções anônimas no processamento interno "
            f"são permitidas."
        )
