from pathlib import Path

from nucleus.rules.scanner.planet_scanner import PlanetScanner


def _build(
    root: Path,
    planet_path: str,
    files=(),
    directories=()
) -> None:

    planet = root / planet_path

    planet.mkdir(parents=True, exist_ok=True)

    for name in files:
        (planet / name).write_text("", encoding="utf-8")

    for name in directories:
        (planet / name).mkdir(parents=True, exist_ok=True)


def test_scanner_describes_planet_structure(tmp_path):

    _build(
        tmp_path,
        "planets/user",
        files=["routes.py"],
        directories=["controllers", "repository", "usecases"]
    )

    planets = PlanetScanner(tmp_path).scan()

    assert len(planets) == 1

    planet = planets[0]

    assert planet.name == "user"
    assert planet.path == "planets/user"
    assert planet.files == frozenset({"routes.py"})
    assert planet.directories == frozenset(
        {"controllers", "repository", "usecases"}
    )


# layout real: orbits/planets/<planet>
def test_scanner_finds_planet_inside_orbits(tmp_path):

    _build(
        tmp_path,
        "orbits/planets/auth",
        files=["routes.py"],
        directories=["controllers", "repository", "usecases"]
    )

    planets = PlanetScanner(tmp_path).scan()

    assert len(planets) == 1
    assert planets[0].name == "auth"
    assert planets[0].path == "orbits/planets/auth"


# diretorios que nao estao sob "planets" nao sao Planets
def test_scanner_ignores_non_planet_directories(tmp_path):

    _build(
        tmp_path,
        "orbits/database/models",
        files=["user_model.py"]
    )

    # "controllers" esta DENTRO do Planet user: nao e um Planet
    _build(
        tmp_path,
        "planets/user/controllers",
        files=["user_controller.py"]
    )

    planets = PlanetScanner(tmp_path).scan()

    assert [planet.name for planet in planets] == ["user"]


# varios planets sao descritos individualmente
def test_scanner_describes_multiple_planets(tmp_path):

    _build(tmp_path, "planets/user", directories=["usecases"])
    _build(tmp_path, "planets/auth", directories=["usecases"])

    planets = PlanetScanner(tmp_path).scan()

    assert sorted(planet.name for planet in planets) == [
        "auth",
        "user",
    ]


# __pycache__ nao faz parte da estrutura do Planet
def test_scanner_ignores_pycache(tmp_path):

    _build(
        tmp_path,
        "planets/user",
        files=["routes.py"],
        directories=["__pycache__", "usecases"]
    )

    planet = PlanetScanner(tmp_path).scan()[0]

    assert "__pycache__" not in planet.directories
