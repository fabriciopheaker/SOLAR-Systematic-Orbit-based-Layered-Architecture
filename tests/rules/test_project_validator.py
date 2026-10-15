import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules import architecture
from nucleus.rules.project_validator import (
    Check,
    ProjectValidator,
    project_checks,
)
from nucleus.rules.report import (
    CORRECT,
    VIOLATION,
    CheckResult,
    ProjectReport,
    Violation,
)
from nucleus.rules.rule import Rule


# ---------------------------------------------------------------------
# Apoio
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Target:
    """
    Alvo de teste, com local — como os contextos reais.
    """

    file: str
    line: int


class FakeScanner:
    """
    Scanner que devolve alvos fixos.
    """

    def __init__(self, root: Path, targets=()):
        self.targets = list(targets)

    def scan(self):
        return list(self.targets)


class AlwaysFails(Rule):

    def code(self) -> str:
        return "FAKE-001"

    def description(self) -> str:
        return "regra de teste que sempre falha."

    def validate(self, target) -> None:
        raise SolarException(f"falhou em {target.file}:{target.line}")


class NeverFails(AlwaysFails):

    def code(self) -> str:
        return "FAKE-002"

    def validate(self, target) -> None:
        return


def _module_rules() -> dict[str, Rule]:
    """
    Descobre TODAS as regras escritas em architecture/.
    """

    found: dict[str, Rule] = {}

    for module_info in pkgutil.iter_modules(architecture.__path__):

        module = importlib.import_module(
            f"{architecture.__name__}.{module_info.name}"
        )

        for value in vars(module).values():

            if not isinstance(value, type):
                continue

            if not issubclass(value, Rule) or value is Rule:
                continue

            rule = value()

            found[rule.code()] = rule

    return found


# ---------------------------------------------------------------------
# Coleta sem parar na primeira violação
# ---------------------------------------------------------------------

# o RuleEngine para na primeira; o validador mostra TUDO de uma vez
def test_all_violations_are_collected(tmp_path):

    targets = [
        Target("a.py", 1),
        Target("a.py", 2),
        Target("a.py", 3),
    ]

    check = Check(
        name="Fake",
        scanner=lambda root: FakeScanner(root, targets),
        rules=(AlwaysFails(),)
    )

    report = ProjectValidator(tmp_path, checks=[check]).validate()

    assert len(report.violations) == 3


def test_every_rule_of_a_check_is_applied(tmp_path):

    check = Check(
        name="Fake",
        scanner=lambda root: FakeScanner(tmp_path, [Target("a.py", 1)]),
        rules=(AlwaysFails(), NeverFails(), AlwaysFails())
    )

    report = ProjectValidator(tmp_path, checks=[check]).validate()

    assert [item.rule for item in report.violations] == ["FAKE-001", "FAKE-001"]


def test_clean_check_produces_a_clean_report(tmp_path):

    check = Check(
        name="Fake",
        scanner=lambda root: FakeScanner(tmp_path, [Target("a.py", 1)]),
        rules=(NeverFails(),)
    )

    report = ProjectValidator(tmp_path, checks=[check]).validate()

    assert report.is_clean() is True
    assert report.violations == ()


# ---------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------

def test_report_carries_the_location(tmp_path):

    check = Check(
        name="Fake",
        scanner=lambda root: FakeScanner(root, [Target("a.py", 7)]),
        rules=(AlwaysFails(),)
    )

    violation = ProjectValidator(
        tmp_path,
        checks=[check]
    ).validate().violations[0]

    assert violation.rule == "FAKE-001"
    assert violation.location == "a.py:7"


def test_report_groups_by_rule(tmp_path):

    check = Check(
        name="Fake",
        scanner=lambda root: FakeScanner(
            root,
            [Target("a.py", 1), Target("b.py", 2)]
        ),
        rules=(AlwaysFails(),)
    )

    report = ProjectValidator(tmp_path, checks=[check]).validate()

    assert list(report.by_rule()) == ["FAKE-001"]
    assert len(report.by_rule()["FAKE-001"]) == 2
    assert report.rules_violated() == 1


def test_report_text_shows_the_violating_rules(tmp_path):

    check = Check(
        name="Fake",
        scanner=lambda root: FakeScanner(root, [Target("a.py", 1)]),
        rules=(AlwaysFails(),)
    )

    text = str(ProjectValidator(tmp_path, checks=[check]).validate())

    assert "FAKE-001" in text
    assert "regra de teste" in text
    assert f"resultado: {VIOLATION}" in text


# ---------------------------------------------------------------------
# Status em palavra
# ---------------------------------------------------------------------

def test_check_status_is_correct_when_clean():

    assert CheckResult(name="Fake").status() == CORRECT


def test_check_status_is_violation_when_not_clean():

    result = CheckResult(
        name="Fake",
        violations=(
            Violation(
                rule="FAKE-001",
                description="regra de teste",
                message="falhou",
                location="a.py:1"
            ),
        )
    )

    assert result.status() == VIOLATION


# a saida lista CADA verificacao com o seu status
# (em vez de so mostrar o que falhou)
def test_report_lists_every_check_with_its_status(tmp_path):

    clean = Check(
        name="Limpo",
        scanner=lambda root: FakeScanner(root),
        rules=(NeverFails(),)
    )

    broken = Check(
        name="Quebrado",
        scanner=lambda root: FakeScanner(root, [Target("a.py", 1)]),
        rules=(AlwaysFails(),)
    )

    text = str(
        ProjectValidator(
            tmp_path,
            checks=[clean, broken]
        ).validate()
    )

    assert "Limpo" in text and CORRECT in text
    assert "Quebrado" in text and VIOLATION in text


def test_clean_report_says_correct(tmp_path):

    check = Check(
        name="Fake",
        scanner=lambda root: FakeScanner(root),
        rules=(NeverFails(),)
    )

    report = ProjectValidator(tmp_path, checks=[check]).validate()

    assert report.status() == CORRECT
    assert f"resultado: {CORRECT}" in str(report)


def test_empty_report_does_not_explode():

    assert "sem verificações" in str(ProjectReport())


# ---------------------------------------------------------------------
# O registro precisa cobrir todas as regras
# ---------------------------------------------------------------------

# regras sem scanner estatico: o contexto delas e montado em outro
# lugar que nao a varredura do codigo
RULES_WITHOUT_SCANNER = frozenset({
    "SOLAR-ARCH-004",
    "SOLAR-ARCH-015",
})


# escrever uma regra nova e esquecer de registra-la passa a ser
# impossivel: este teste falha
def test_every_rule_is_registered():

    registered = {
        rule.code()
        for check in project_checks()
        for rule in check.rules
    }

    expected = set(_module_rules()) - RULES_WITHOUT_SCANNER

    assert registered == expected


def test_no_rule_is_registered_twice():

    codes = [
        rule.code()
        for check in project_checks()
        for rule in check.rules
    ]

    assert len(codes) == len(set(codes))


def test_each_check_group_is_not_empty():

    for check in project_checks():

        assert check.rules, f"{check.name} sem regras"
        assert check.name
