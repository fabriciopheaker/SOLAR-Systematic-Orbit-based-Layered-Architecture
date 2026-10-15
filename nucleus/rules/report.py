# Estrutura do relatório de verificação arquitetural.
#
# Três níveis, do menor para o maior:
#
#     Violation       uma regra violada, com a mensagem da própria
#                     regra e o local do alvo;
#     CheckResult     o resultado de UM contexto (um scanner);
#     ProjectReport   todos os contextos — é ele que o `check`
#                     imprime e que os testes inspecionam.
#
# Tudo aqui é `frozen`: relatório é REGISTRO do que foi
# encontrado, não estado a ser alterado durante a exibição.
from dataclasses import dataclass


# Os dois status possíveis, em palavra. Constantes e não `enum`
# porque o relatório é texto: o `check` usa o status direto no nome
# do arquivo de auditoria ("...-correct.md").
CORRECT = "correct"
VIOLATION = "violation"


@dataclass(frozen=True)
class Violation:
    """
    Uma violação arquitetural encontrada.

    rule:
        Código da regra (ex.: "SOLAR-ARCH-019").

    description:
        Descrição da regra, para agrupar o relatório.

    message:
        A mensagem da própria regra — é ela que diz onde e o que
        fazer. O validador NÃO reescreve essa mensagem.

    location:
        Local do alvo, quando o contexto informa
        (ex.: "orbits/database/models/user_model.py:12").
    """

    rule: str
    description: str
    message: str

    # Opcional: alguns contextos não carregam local, e aí é a
    # própria mensagem da regra que diz onde é.
    location: str = ""


@dataclass(frozen=True)
class CheckResult:
    """
    O resultado de UMA verificação.

    name:
        Nome do contexto verificado (ex.: "PlanetStructure").

    violations:
        O que essa verificação encontrou.
    """

    name: str

    # Vazio significa correto — é a única condição de sucesso, e é
    # por isso que `is_correct` pode ser uma negação.
    violations: tuple[Violation, ...] = ()

    def is_correct(self) -> bool:
        """
        Indica se a verificação passou.
        """

        return not self.violations

    def status(self) -> str:
        """
        Status em palavra: `correct` ou `violation`.
        """

        return CORRECT if self.is_correct() else VIOLATION


@dataclass(frozen=True)
class ProjectReport:
    """
    Resultado de uma verificação arquitetural completa.

    results:
        O resultado de cada verificação, na ordem de execução.

    rules:
        Quantidade de regras aplicadas.
    """

    results: tuple[CheckResult, ...] = ()
    rules: int = 0

    # `property` e não campo: é uma VISÃO de `results`, derivada
    # na hora da leitura. Guardar a lista achatada abriria a
    # chance de ela divergir de `results`.
    @property
    def violations(self) -> tuple[Violation, ...]:
        """
        Todas as violações, sem agrupamento.
        """

        return tuple(
            violation
            for result in self.results
            for violation in result.violations
        )

    def is_clean(self) -> bool:
        """
        Indica se o projeto passou em todas as regras.
        """

        return all(result.is_correct() for result in self.results)

    def status(self) -> str:
        """
        Status geral em palavra: `correct` ou `violation`.
        """

        return CORRECT if self.is_clean() else VIOLATION

    def by_rule(self) -> dict[str, tuple[Violation, ...]]:
        """
        Agrupa as violações por código de regra.
        """

        grouped: dict[str, list[Violation]] = {}

        # `setdefault` cobre os dois casos com uma linha: a lista
        # do grupo já existe ou acabou de ser criada.
        for violation in self.violations:
            grouped.setdefault(violation.rule, []).append(violation)

        return {
            rule: tuple(items)
            for rule, items in grouped.items()
        }

    def rules_violated(self) -> int:
        """
        Quantidade de regras que foram violadas.
        """

        return len(self.by_rule())

    def __str__(self) -> str:
        return self._format()

    def _format(self) -> str:

        if not self.results:
            return "SOLAR — verificação arquitetural\n\nsem verificações"

        return "\n".join(self._blocks())

    def _blocks(self) -> list[str]:

        # A coluna do status é alinhada pelo nome mais longo; sem
        # isso o status "dança" conforme o tamanho do nome.
        width = max(len(result.name) for result in self.results)

        blocks = [
            "SOLAR — verificação arquitetural",
            "",
            *(
                f"{result.name.ljust(width)}   {result.status()}"
                for result in self.results
            ),
        ]

        # O detalhe só aparece quando há o que detalhar: um
        # relatório correto é a lista de verificações e o
        # resultado, nada mais.
        if not self.is_clean():
            blocks.extend(["", *self._detail_blocks()])

        # O resumo é sempre a ÚLTIMA linha, e é o que o `check`
        # procura para nomear o arquivo de auditoria.
        blocks.append(self._summary())

        return blocks

    def _detail_blocks(self) -> list[str]:

        return [
            line
            for rule, violations in self.by_rule().items()
            for line in self._rule_block(rule, violations)
        ]

    def _rule_block(
        self,
        rule: str,
        violations: tuple[Violation, ...]
    ) -> list[str]:

        # Descrição da PRIMEIRA violação: todas as violações do
        # grupo são da mesma regra, então a descrição é a mesma —
        # repeti-la em cada linha seria ruído.
        return [
            f"{rule} · {violations[0].description} "
            f"({len(violations)})",
            *(
                f"  {violation.location or '—'}  {violation.message}"
                for violation in violations
            ),
            "",
        ]

    def _summary(self) -> str:

        # O projeto todo passa: nem número de violações nem
        # contagem de regras aparecem — a ausência delas é o
        # sinal de que está tudo certo.
        if self.is_clean():
            return f"resultado: {CORRECT}"

        return (
            f"resultado: {VIOLATION} — "
            f"{len(self.violations)} violação(ões) "
            f"em {self.rules_violated()} regra(s)"
        )
