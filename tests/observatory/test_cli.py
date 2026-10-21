import subprocess
import sys
from pathlib import Path

from observatory.solar.cli import CLEAN, UNKNOWN_COMMAND, main
from observatory.solar.commands.check import (
    CLEAN as CHECK_CLEAN,
    INVALID_ROOT,
    VIOLATIONS,
)


def _planet(root: Path, name: str, complete: bool) -> None:
    """
    Cria um Planet, completo ou não.
    """

    path = root / "planets" / name
    path.mkdir(parents=True)

    if complete:
        (path / "__init__.py").write_text("", encoding="utf-8")
        (path / "routes.py").write_text("", encoding="utf-8")

        for directory in (
            "atmosphere",
            "controllers",
            "entity",
            "repository",
            "resources",
            "usecases",
        ):
            (path / directory).mkdir()


def _project_root() -> Path:
    """
    Raiz do projeto: o diretório que tem nucleus/ e observatory/.
    """

    for parent in Path(__file__).resolve().parents:

        if (
            (parent / "nucleus").is_dir()
            and (parent / "observatory" / "solar" / "__main__.py").is_file()
        ):
            return parent

    raise AssertionError("raiz do projeto não encontrada")


def _command(*arguments: str) -> list[str]:
    """
    O comando como ele é digitado.
    """

    return [
        sys.executable,
        str(Path("observatory", "solar")),
        *arguments,
    ]


# ---------------------------------------------------------------------
# Despacho de comandos
# ---------------------------------------------------------------------

def test_usage_is_printed_without_arguments(capsys):

    assert main([]) == CLEAN
    assert "uso: python observatory/solar" in capsys.readouterr().out


def test_help_is_printed(capsys):

    assert main(["--help"]) == CLEAN
    assert "observatory/solar check" in capsys.readouterr().out


def test_unknown_command_is_reported(capsys):

    assert main(["verificar"]) == UNKNOWN_COMMAND

    captured = capsys.readouterr()

    assert "comando desconhecido: verificar" in captured.err
    assert "uso: python observatory/solar" in captured.err


# ---------------------------------------------------------------------
# check
# ---------------------------------------------------------------------

def test_check_is_correct_on_a_conforming_project(tmp_path, capsys):

    _planet(tmp_path, "user", complete=True)

    assert main(["check", str(tmp_path)]) == CHECK_CLEAN
    assert "resultado: correct" in capsys.readouterr().out


# a SOLAR-ROF-006 acusa o Planet sem a estrutura padrão
def test_check_is_violation_on_a_broken_project(tmp_path, capsys):

    _planet(tmp_path, "user", complete=False)

    assert main(["check", str(tmp_path)]) == VIOLATIONS

    output = capsys.readouterr().out

    assert "resultado: violation" in output
    assert "SOLAR-ROF-006" in output
    assert "PlanetStructure" in output


# a saida mostra o status de CADA verificacao
def test_check_output_lists_every_check(tmp_path, capsys):

    _planet(tmp_path, "user", complete=False)

    main(["check", str(tmp_path)])

    output = capsys.readouterr().out

    assert "PlanetStructure" in output
    assert "Dependency" in output
    assert "correct" in output
    assert "violation" in output


def test_check_rejects_an_invalid_path(tmp_path, capsys):

    assert main(["check", str(tmp_path / "nao-existe")]) == INVALID_ROOT
    assert "caminho inválido" in capsys.readouterr().err


def test_check_prints_its_own_usage(capsys):

    assert main(["check", "--help"]) == CHECK_CLEAN
    assert "uso: python observatory/solar check" in capsys.readouterr().out


def test_check_verifies_the_current_directory_by_default(
    tmp_path,
    monkeypatch,
    capsys
):

    _planet(tmp_path, "user", complete=True)

    monkeypatch.chdir(tmp_path)

    assert main(["check"]) == CHECK_CLEAN
    assert "resultado: correct" in capsys.readouterr().out


# ---------------------------------------------------------------------
# Auditoria: o comando informa onde o registro ficou
# ---------------------------------------------------------------------

# sem violacao o registro TAMBEM e gravado: e ele que garante
# que a ultima verificacao aconteceu e passou
def test_check_announces_audit_when_clean(tmp_path, capsys):

    _planet(tmp_path, "user", complete=True)

    main(["check", str(tmp_path)])

    output = capsys.readouterr().out

    assert "auditoria:" in output
    assert "correct.md" in output


def test_check_writes_the_audit_file(tmp_path):

    _planet(tmp_path, "user", complete=False)

    main(["check", str(tmp_path)])

    records = list(
        (tmp_path / "observatory" / "solar" / "check").glob("*.md")
    )

    assert len(records) == 1
    assert records[0].name.endswith("-violation.md")
    assert "SOLAR-ROF-006" in records[0].read_text(encoding="utf-8")


def test_check_writes_a_correct_record_too(tmp_path):

    _planet(tmp_path, "user", complete=True)

    main(["check", str(tmp_path)])

    records = list(
        (tmp_path / "observatory" / "solar" / "check").glob("*.md")
    )

    assert len(records) == 1
    assert records[0].name.endswith("-correct.md")
    assert "| resultado | correct |" in records[0].read_text(
        encoding="utf-8"
    )


# ---------------------------------------------------------------------
# O comando de verdade: `python observatory/solar check`
# ---------------------------------------------------------------------

# este teste existe porque ao executar um DIRETORIO o Python aponta o
# sys.path para dentro dele — sem o ajuste do __main__.py,
# `import nucleus` falharia. So um processo de verdade prova isso.
def test_runs_as_python_observatory_solar(tmp_path):

    _planet(tmp_path, "user", complete=True)

    result = subprocess.run(
        _command("check", str(tmp_path)),
        cwd=_project_root(),
        capture_output=True,
        text=True
    )

    assert result.returncode == CHECK_CLEAN
    assert "resultado: correct" in result.stdout


def test_python_observatory_solar_fails_on_a_broken_project(tmp_path):

    _planet(tmp_path, "user", complete=False)

    result = subprocess.run(
        _command("check", str(tmp_path)),
        cwd=_project_root(),
        capture_output=True,
        text=True
    )

    assert result.returncode == VIOLATIONS
    assert "resultado: violation" in result.stdout
