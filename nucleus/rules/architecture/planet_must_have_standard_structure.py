# SOLAR-ARCH-019 — a FORMA do Planet.
#
# É a regra mais estrutural do catálogo: não olha conteúdo nem
# dependência, só se as peças existem e se cada uma é arquivo ou
# diretório. Existe porque a arquitetura só é navegável se todo
# Planet for reconhecível à primeira vista.
#
# O `routes.py` já é fiscalizado quanto à LOCALIZAÇÃO pela
# SOLAR-ARCH-018; aqui ele é exigido como peça do Planet.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import Rule
from nucleus.rules.scanner.planet_structure import PlanetStructure


class PlanetMustHaveStandardStructure(Rule):
    """
    Regra arquitetural:

    SOLAR-ARCH-019

    TODO Planet deve possuir a estrutura padrão:

        planets/<planet>/
        ├── __init__.py        → pacote do Planet
        ├── routes.py          → rotas do Planet
        ├── atmosphere/        → fronteira de entrada do Planet
        ├── controllers/       → Controllers do Planet
        ├── entity/            → entidades do Planet
        ├── repository/        → repositório do Planet
        ├── resources/         → Resources do Planet
        └── usecases/          → UseCases do Planet

    A `atmosphere/` é a fronteira de ENTRADA: é lá que moram os
    guardas específicos do Planet (`sanitizers/` e `validators/`), e é
    a ROTA que declara qual deles protege cada entrada. O Controller
    recebe a requisição já tratada, e por isso não conhece essa pasta.

    Convenções associadas (não contadas por esta regra):

        controllers/user_controller.py      → um Controller por Planet;
        repository/user_repository.py       → UM repository por Planet;
        atmosphere/sanitizers/              → os guardas específicos.

    É VIOLAÇÃO:

        planets/user/repository.py          → repository é DIRETÓRIO,
                                              não arquivo solto;
        planets/user/                        → sem as peças obrigatórias.

    Exemplo válido:

        planets/user/
        ├── __init__.py
        ├── routes.py
        ├── atmosphere/
        │   ├── __init__.py
        │   ├── sanitizers/
        │   └── validators/
        ├── controllers/
        │   └── user_controller.py
        ├── entity/
        │   └── user_entity.py
        ├── repository/
        │   └── user_repository.py
        ├── resources/
        │   └── user_resource.py
        └── usecases/
            └── create_user.py

    O `routes.py` já é fiscalizado quanto à LOCALIZAÇÃO pela
    SOLAR-ARCH-018; aqui ele é exigido como peça do Planet.

    ESCOPO — o que esta regra NÃO cobre:

    Não proíbe arquivos ou diretórios extras dentro do Planet
    (ex.: `entity.py`, `__init__.py`). A regra apenas exige as
    peças obrigatórias e o formato (diretório x arquivo).
    """

    # Peças obrigatórias como ARQUIVO.
    #
    # A separação entre ARQUIVO e DIRETÓRIO é o que a regra fiscaliza
    # além da presença: um `repository.py` solto não satisfaz o
    # diretório exigido abaixo.
    REQUIRED_FILES = (
        "__init__.py",
        "routes.py",
    )

    # Peças obrigatórias como DIRETÓRIO.
    #
    # O sufixo `/` aparece na MENSAGEM (`repository/`) para deixar
    # claro que falta um diretório, e não um arquivo — a lista aqui
    # fica sem o sufixo.
    REQUIRED_DIRECTORIES = (
        "atmosphere",
        "controllers",
        "entity",
        "repository",
        "resources",
        "usecases",
    )

    def code(self) -> str:
        return "SOLAR-ARCH-019"

    def description(self) -> str:
        return (
            "Todo Planet deve possuir a estrutura padrão: "
            "__init__.py, routes.py, atmosphere/, controllers/, "
            "entity/, repository/, resources/ e usecases/."
        )

    def validate(self, planet: PlanetStructure) -> None:

        # Acumula TODAS as peças ausentes: se a regra parasse na
        # primeira, um Planet novo sem nada seria acusado 7 vezes,
        # uma por rodada do check, para descobrir o mesmo problema.
        missing = self._missing(planet)

        if not missing:
            return

        raise SolarException(
            self._build_message(planet, missing)
        )

    def _missing(self, planet: PlanetStructure) -> list[str]:

        missing: list[str] = []

        # Os dois laços consultam listas DIFERENTES do contexto
        # (`files` x `directories`) — é essa separação que faz um
        # `repository.py` solto não contar como `repository/`.
        for name in self.REQUIRED_FILES:
            if name not in planet.files:
                missing.append(name)

        # `/` no fim apenas para a MENSAGEM: quem lê o relatório
        # precisa saber que falta um diretório.
        for name in self.REQUIRED_DIRECTORIES:
            if name not in planet.directories:
                missing.append(f"{name}/")

        return missing

    def _build_message(
        self,
        planet: PlanetStructure,
        missing: list[str]
    ) -> str:

        # A estrutura COMPLETA vai na mensagem, e não só o que falta:
        # quem vai criar o Planet precisa do conjunto todo, e não da
        # diferença.
        expected = ", ".join(
            list(self.REQUIRED_FILES)
            + [f"{name}/" for name in self.REQUIRED_DIRECTORIES]
        )

        return (
            f"{self.code()}: "
            f"o Planet '{planet.name}' ({planet.path}) não possui "
            f"{', '.join(missing)}. "
            f"Estrutura esperada: {expected}."
        )
