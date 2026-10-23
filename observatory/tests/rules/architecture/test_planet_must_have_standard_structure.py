from pathlib import Path

import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.planet_must_have_standard_structure import (
    PlanetMustHaveStandardStructure
)
from nucleus.rules.scanner.planet_scanner import PlanetScanner
from nucleus.rules.scanner.planet_structure import PlanetStructure


def _planet(
    files: set[str] | None = None,
    directories: set[str] | None = None
) -> PlanetStructure:

    return PlanetStructure(
        name="user",
        path="planets/user",
        files=frozenset(
            files if files is not None else {"__init__.py", "routes.py"}
        ),
        directories=frozenset(
            directories
            if directories is not None
            else {
                "atmosphere",
                "controllers",
                "entity",
                "repository",
                "resources",
                "usecases",
            }
        )
    )


def _build(root: Path, planet_path: str) -> None:

    planet = root / planet_path

    planet.mkdir(parents=True, exist_ok=True)

    (planet / "__init__.py").write_text("", encoding="utf-8")
    (planet / "routes.py").write_text("", encoding="utf-8")

    for name in (
        "atmosphere",
        "controllers",
        "entity",
        "repository",
        "resources",
        "usecases",
    ):
        (planet / name).mkdir(parents=True, exist_ok=True)


# estrutura completa e valida
def test_complete_planet_structure_is_allowed():

    rule = PlanetMustHaveStandardStructure()

    rule.validate(_planet())


# arquivos/diretorios extras nao sao violacao
def test_extra_entries_are_allowed():

    rule = PlanetMustHaveStandardStructure()

    rule.validate(
        _planet(
            files={"routes.py", "entity.py", "__init__.py"},
            directories={
                "atmosphere",
                "controllers",
                "entity",
                "repository",
                "resources",
                "usecases",
                "exceptions",
            }
        )
    )


# sem routes.py o Planet e invalido
def test_missing_routes_file_is_rejected():

    rule = PlanetMustHaveStandardStructure()

    with pytest.raises(SolarException):
        rule.validate(_planet(files=set()))


# sem controllers/ o Planet e invalido
def test_missing_controllers_directory_is_rejected():

    rule = PlanetMustHaveStandardStructure()

    with pytest.raises(SolarException):
        rule.validate(
            _planet(directories={"repository", "usecases"})
        )


# sem repository/ o Planet e invalido
def test_missing_repository_directory_is_rejected():

    rule = PlanetMustHaveStandardStructure()

    with pytest.raises(SolarException):
        rule.validate(
            _planet(directories={"controllers", "usecases"})
        )


# sem usecases/ o Planet e invalido
def test_missing_usecases_directory_is_rejected():

    rule = PlanetMustHaveStandardStructure()

    with pytest.raises(SolarException):
        rule.validate(
            _planet(directories={"controllers", "repository"})
        )


# sem entity/ o Planet e invalido
def test_missing_entity_directory_is_rejected():

    rule = PlanetMustHaveStandardStructure()

    with pytest.raises(SolarException):
        rule.validate(
            _planet(
                directories={
                    "controllers",
                    "repository",
                    "resources",
                    "usecases",
                }
            )
        )


# sem resources/ o Planet e invalido
def test_missing_resources_directory_is_rejected():

    rule = PlanetMustHaveStandardStructure()

    with pytest.raises(SolarException):
        rule.validate(
            _planet(
                directories={
                    "controllers",
                    "entity",
                    "repository",
                    "usecases",
                }
            )
        )


# sem __init__.py o Planet e invalido
def test_missing_init_file_is_rejected():

    rule = PlanetMustHaveStandardStructure()

    with pytest.raises(SolarException):
        rule.validate(_planet(files={"routes.py"}))


# repository.py como ARQUIVO solto e violacao
# (repository deve ser DIRETORIO)
def test_repository_as_file_is_rejected():

    rule = PlanetMustHaveStandardStructure()

    with pytest.raises(SolarException):
        rule.validate(
            _planet(
                files={"routes.py", "repository.py"},
                directories={"controllers", "usecases"}
            )
        )


# usecases.py como ARQUIVO solto e violacao
def test_usecases_as_file_is_rejected():

    rule = PlanetMustHaveStandardStructure()

    with pytest.raises(SolarException):
        rule.validate(
            _planet(
                files={"routes.py", "usecases.py"},
                directories={"controllers", "repository"}
            )
        )


# integracao: estrutura real no disco passa pela regra
def test_scanned_planet_structure_is_allowed(tmp_path):

    _build(tmp_path, "planets/user")

    planets = PlanetScanner(tmp_path).scan()

    assert planets

    rule = PlanetMustHaveStandardStructure()

    for planet in planets:
        rule.validate(planet)


# integracao: Planet incompleto no disco e rejeitado
def test_scanned_incomplete_planet_is_rejected(tmp_path):

    planet = tmp_path / "planets/user"
    planet.mkdir(parents=True, exist_ok=True)

    (planet / "user_repository.py").write_text("", encoding="utf-8")

    planets = PlanetScanner(tmp_path).scan()

    assert planets

    rule = PlanetMustHaveStandardStructure()

    with pytest.raises(SolarException):
        rule.validate(planets[0])
