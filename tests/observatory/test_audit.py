from datetime import datetime
from pathlib import Path

from nucleus.rules.report import (
    CheckResult,
    ProjectReport,
    Violation,
)
from observatory.solar import audit


MOMENT = datetime(2026, 10, 5, 14, 30, 0, tzinfo=audit.TIME_ZONE)


def _violation() -> Violation:

    return Violation(
        rule="SOLAR-ARCH-019",
        description=(
            "Todo Planet deve possuir a estrutura padrão: "
            "routes.py, controllers/, repository/ e usecases/."
        ),
        message=(
            "SOLAR-ARCH-019: o Planet 'user' não possui routes.py, "
            "controllers/, repository/, usecases/."
        ),
        location="orbits/planets/user"
    )


def _report(*violations: Violation) -> ProjectReport:

    return ProjectReport(
        results=(
            CheckResult(name="Dependency"),
            CheckResult(name="PlanetStructure", violations=violations),
            CheckResult(name="UnsafeSql"),
        ),
        rules=3
    )


def _audit_root(root: Path) -> Path:

    return root / "observatory" / "solar" / "check"


def _records(root: Path) -> list[Path]:

    return sorted(_audit_root(root).glob("*.md"))


# ---------------------------------------------------------------------
# Quando registra
# ---------------------------------------------------------------------

# o registro da ultima execucao e o que garante que ela ACONTECEU:
# se so a violacao gerasse arquivo, "nenhum arquivo novo" seria
# ambiguo entre "esta tudo certo" e "ninguem rodou"
def test_clean_run_also_writes(tmp_path):

    path = audit.record(_report(), tmp_path, MOMENT)

    assert path.is_file()
    assert len(_records(tmp_path)) == 1


def test_violation_writes_a_markdown_file(tmp_path):

    path = audit.record(_report(_violation()), tmp_path, MOMENT)

    assert path.is_file()
    assert path.suffix == ".md"
    assert path.parent == _audit_root(tmp_path)


# o registro fica ao lado do comando que o produziu
def test_audit_directory_is_beside_the_command(tmp_path):

    assert audit.audit_directory(tmp_path) == (
        tmp_path / "observatory" / "solar" / "check"
    )


def test_directory_is_created_when_missing(tmp_path):

    assert not (tmp_path / "observatory").exists()

    audit.record(_report(_violation()), tmp_path, MOMENT)

    assert _audit_root(tmp_path).is_dir()


# ---------------------------------------------------------------------
# Nome do arquivo
# ---------------------------------------------------------------------

# o nome carrega o momento E o resultado: o arquivo mais recente
# diz, sem precisar abrir, se a ultima verificacao passou
def test_filename_carries_the_moment_and_the_result(tmp_path):

    path = audit.record(_report(_violation()), tmp_path, MOMENT)

    assert path.name == "check-2026-10-05-143000-violation.md"


def test_correct_filename_carries_the_result(tmp_path):

    path = audit.record(_report(), tmp_path, MOMENT)

    assert path.name == "check-2026-10-05-143000-correct.md"


# duas execucoes no mesmo segundo NAO podem se sobrescrever: um
# registro de auditoria perdido e pior do que um nome feio
def test_same_moment_does_not_overwrite(tmp_path):

    first = audit.record(_report(_violation()), tmp_path, MOMENT)
    second = audit.record(_report(_violation()), tmp_path, MOMENT)

    assert first != second
    assert len(_records(tmp_path)) == 2
    assert second.name == "check-2026-10-05-143000-violation-2.md"


# a ordem de nome e a ordem cronologica: o ultimo arquivo e a
# ultima verificacao
def test_files_are_ordered_by_name(tmp_path):

    later = datetime(2026, 10, 5, 15, 0, 0, tzinfo=audit.TIME_ZONE)

    audit.record(_report(_violation()), tmp_path, MOMENT)
    audit.record(_report(), tmp_path, later)

    assert [path.name for path in _records(tmp_path)] == [
        "check-2026-10-05-143000-violation.md",
        "check-2026-10-05-150000-correct.md",
    ]


# ---------------------------------------------------------------------
# Registro da SUBIDA: so quando ha violacao
# ---------------------------------------------------------------------

# a verificacao da subida roda sozinha: gravar a cada vez encheria o
# diretorio de arquivos identicos e afogaria o registro que importa
# (o da violacao)
def test_record_violation_skips_a_clean_report(tmp_path):

    path = audit.record_violation(_report(), tmp_path, MOMENT)

    assert path is None
    assert _records(tmp_path) == []


def test_record_violation_writes_when_there_is_violation(tmp_path):

    path = audit.record_violation(_report(_violation()), tmp_path, MOMENT)

    assert path is not None
    assert path.name == "check-2026-10-05-143000-violation.md"
    assert len(_records(tmp_path)) == 1


# o CONTEUDO e o mesmo do registro do comando: a politica muda, o
# registro nao
#
# `root` normalizado porque os dois renderizam o caminho resolvido
# da raiz, e o `tmp_path` do pytest e um caminho com symlink no
# macOS — comparar os textos crus falharia lá, sem nada de errado
# aqui
def test_record_violation_writes_the_same_content_as_record(tmp_path):

    root = tmp_path.resolve()

    from_cli = audit.record(_report(_violation()), root, MOMENT)
    from_server = audit.record_violation(_report(_violation()), root, MOMENT)

    assert from_cli.read_text(encoding="utf-8") == (
        from_server.read_text(encoding="utf-8")
    )


# ---------------------------------------------------------------------
# Caminho mostrado
# ---------------------------------------------------------------------

# relativo: quem le a linha e uma pessoa
#
# `root` normalizado pelo mesmo motivo do teste acima

def test_display_path_is_relative_when_inside(tmp_path, monkeypatch):

    root = tmp_path.resolve()

    monkeypatch.chdir(root)

    inside = root / "observatory" / "solar" / "check" / "check-x.md"

    assert audit.display_path(inside) == Path(
        "observatory/solar/check/check-x.md"
    )


# absoluto: o registro ficou fora do diretorio atual, e so o caminho
# completo diz onde ele esta
def test_display_path_is_absolute_when_outside(
    tmp_path_factory,
    monkeypatch
):

    here = tmp_path_factory.mktemp("here")
    other = tmp_path_factory.mktemp("other")

    monkeypatch.chdir(here)

    outside = other / "check-x.md"

    assert audit.display_path(outside) == outside


# ---------------------------------------------------------------------
# Hora de São Paulo
# ---------------------------------------------------------------------

def test_time_zone_is_sao_paulo():

    assert audit.TIME_ZONE_LABEL == "America/Sao_Paulo"

    # o deslocamento so existe COM uma data: `utcoffset(None)`
    # devolve None
    moment = datetime(2026, 10, 5, 14, 30, tzinfo=audit.TIME_ZONE)

    assert moment.utcoffset().total_seconds() == -3 * 3600
    assert moment.strftime("%H:%M") == "14:30"


# sem horario informado, o registro usa a hora de Sao Paulo
def test_default_moment_uses_sao_paulo(tmp_path):

    path = audit.record(_report(), tmp_path)

    content = path.read_text(encoding="utf-8")

    assert "(America/Sao_Paulo)" in content


# ---------------------------------------------------------------------
# Conteúdo
# ---------------------------------------------------------------------

def test_content_has_the_summary(tmp_path):

    path = audit.record(_report(_violation()), tmp_path, MOMENT)

    content = path.read_text(encoding="utf-8")

    assert "# SOLAR — auditoria da verificação arquitetural" in content
    assert "| resultado | violation |" in content
    assert "| gerado em | 2026-10-05 14:30:00 (America/Sao_Paulo) |" in content
    assert "| violações | 1 |" in content
    assert "| regras violadas | 1 |" in content


# saber o que PASSOU vale tanto quanto saber o que falhou
def test_content_lists_every_check(tmp_path):

    path = audit.record(_report(_violation()), tmp_path, MOMENT)

    content = path.read_text(encoding="utf-8")

    assert "| Dependency | correct |" in content
    assert "| PlanetStructure | violation |" in content
    assert "| UnsafeSql | correct |" in content


def test_content_has_the_violation_details(tmp_path):

    path = audit.record(_report(_violation()), tmp_path, MOMENT)

    content = path.read_text(encoding="utf-8")

    assert "### SOLAR-ARCH-019" in content
    assert "estrutura padrão" in content
    assert "orbits/planets/user" in content
    assert "não possui routes.py" in content
    assert "(1)" in content


def test_content_resolves_the_root_path(tmp_path):

    path = audit.record(_report(_violation()), tmp_path, MOMENT)

    content = path.read_text(encoding="utf-8")

    assert f"| raiz verificada | {tmp_path.resolve()} |" in content
