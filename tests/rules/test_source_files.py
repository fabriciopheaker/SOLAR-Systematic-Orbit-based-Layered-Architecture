from pathlib import Path

from nucleus.rules.project_validator import ProjectValidator
from nucleus.rules.scanner.planet_scanner import PlanetScanner
from nucleus.rules.scanner.source_files import (
    DEFAULT_EXCLUDED_DIRECTORIES,
    belongs_to_project,
    is_inside_excluded,
    is_test_file,
    resolve_exclusions,
    source_files,
)


def _write(root: Path, name: str, content: str = "") -> Path:

    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return path


def _relative(root: Path, files: list[Path]) -> list[str]:

    return [
        file.relative_to(root).as_posix()
        for file in files
    ]


# ---------------------------------------------------------------------
# Nome de arquivo de teste
# ---------------------------------------------------------------------

# os nomes que SÃO teste onde quer que estejam
def test_test_filenames_are_recognized():

    assert is_test_file("conftest.py") is True
    assert is_test_file("test_document.py") is True
    assert is_test_file("document_test.py") is True


# "tests.py" e um arquivo como outro qualquer: o escopo e por
# DIRETORIO, nao por nome parecido
def test_similar_names_are_not_test_files():

    assert is_test_file("tests.py") is False
    assert is_test_file("contest.py") is False
    assert is_test_file("latest.py") is False
    assert is_test_file("testament.py") is False


# ---------------------------------------------------------------------
# O que participa do projeto
# ---------------------------------------------------------------------

def test_file_under_tests_does_not_belong_to_the_project(tmp_path):

    file = _write(tmp_path, "tests/test_document.py")

    assert belongs_to_project(file, tmp_path) is False


def test_conftest_anywhere_does_not_belong_to_the_project(tmp_path):

    file = _write(tmp_path, "conftest.py")

    assert belongs_to_project(file, tmp_path) is False


def test_application_file_belongs_to_the_project(tmp_path):

    file = _write(tmp_path, "orbits/database/models/user_model.py")

    assert belongs_to_project(file, tmp_path) is True


# ---------------------------------------------------------------------
# Varredura
# ---------------------------------------------------------------------

def test_source_files_skips_tests_and_technical_directories(tmp_path):

    _write(tmp_path, "orbits/routes.py")
    _write(tmp_path, "tests/test_routes.py")
    _write(tmp_path, "tests/rules/test_scanner.py")
    _write(tmp_path, "fixtures/config.py")
    _write(tmp_path, "examples/sample.py")
    _write(tmp_path, "__pycache__/cached.py")
    _write(tmp_path, ".venv/lib/installed.py")
    _write(tmp_path, "tests.py")

    assert _relative(tmp_path, source_files(tmp_path)) == [
        "orbits/routes.py",
        "tests.py",
    ]


def test_source_files_are_sorted(tmp_path):

    _write(tmp_path, "zebra.py")
    _write(tmp_path, "alpha.py")
    _write(tmp_path, "meio.py")

    assert _relative(tmp_path, source_files(tmp_path)) == [
        "alpha.py",
        "meio.py",
        "zebra.py",
    ]


def test_exclusions_can_be_replaced(tmp_path):

    _write(tmp_path, "tests/config.py")

    assert source_files(tmp_path, excluded_directories=set()) == [
        tmp_path / "tests" / "config.py"
    ]


# o parametro e sobre DIRETORIOS. Um arquivo com nome de teste
# continua fora mesmo sem exclusao de diretorio: um `test_*.py` no
# meio do codigo de producao e teste do mesmo jeito
def test_test_filenames_are_always_out_of_scope(tmp_path):

    _write(tmp_path, "planets/document/test_document.py")
    _write(tmp_path, "planets/document/document.py")

    assert _relative(
        tmp_path,
        source_files(tmp_path, excluded_directories=set())
    ) == ["planets/document/document.py"]


def test_default_exclusions_cover_tests(tmp_path):

    assert "tests" in DEFAULT_EXCLUDED_DIRECTORIES
    assert "fixtures" in DEFAULT_EXCLUDED_DIRECTORIES
    assert "__pycache__" in DEFAULT_EXCLUDED_DIRECTORIES


def test_resolve_exclusions_uses_the_default_by_default():

    assert resolve_exclusions() == DEFAULT_EXCLUDED_DIRECTORIES
    assert resolve_exclusions(None) == DEFAULT_EXCLUDED_DIRECTORIES


# uma colecao VAZIA substitui o padrao: e como um scanner permite
# desligar a exclusao
def test_resolve_exclusions_accepts_an_empty_collection():

    assert resolve_exclusions(set()) == frozenset()
    assert resolve_exclusions(["custom"]) == frozenset({"custom"})


def test_is_inside_excluded_for_a_directory(tmp_path):

    inside = tmp_path / "tests" / "planets" / "user"
    outside = tmp_path / "orbits" / "planets" / "user"

    assert is_inside_excluded(inside, tmp_path) is True
    assert is_inside_excluded(outside, tmp_path) is False


# ---------------------------------------------------------------------
# O Planet de fixture não é um Planet
# ---------------------------------------------------------------------

def test_planet_inside_tests_is_not_described(tmp_path):

    (tmp_path / "tests" / "planets" / "user").mkdir(parents=True)
    (tmp_path / "planets" / "document").mkdir(parents=True)

    planets = PlanetScanner(tmp_path).scan()

    assert [planet.name for planet in planets] == ["document"]


# ---------------------------------------------------------------------
# De ponta a ponta: o teste pode quebrar as regras
# ---------------------------------------------------------------------

# um projeto cujo UNICO conteudo saiu das regras esta em `tests/`
# nao pode acusar nada
def test_a_project_full_of_broken_tests_is_clean(tmp_path):

    _write(tmp_path, "tests/conftest.py", "import sqlalchemy\n")
    _write(tmp_path, "tests/test_config.py", 'SECRET_KEY = "hardcoded"\n')
    _write(
        tmp_path,
        "tests/fixtures/planets/user/user_repository.py",
        "import sqlalchemy\n"
    )

    report = ProjectValidator(tmp_path).validate()

    assert report.is_clean() is True, report


# e o MESMO conteudo fora de `tests/` continua sendo violacao: se
# este teste passar, o de cima nao esta provando nada
def test_the_same_content_outside_tests_is_flagged(tmp_path):

    _write(tmp_path, "application/config.py", 'SECRET_KEY = "hardcoded"\n')

    report = ProjectValidator(tmp_path).validate()

    assert report.is_clean() is False
    assert "SOLAR-ARCH-020" in report.by_rule()
