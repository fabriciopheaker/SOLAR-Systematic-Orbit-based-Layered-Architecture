# SOLAR-RED-011 — o Planet conhece a FACHADA, não o miolo.
#
# É a versão estreita para Planets do que a SOLAR-RED-008 faz para os
# Orbits: aqui a lista de fachadas permitidas é EXPLÍCITA, porque é o
# Planet que não pode depender de `nucleus.*` interno.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import DEPENDENCY, Rule, rule_code


class PlanetCannotKnowNucleusInfrastructure(Rule):
    """
    Regra arquitetural:

    SOLAR-RED-011

    Planets não devem conhecer detalhes da infraestrutura
    do Nucleus.

    O acesso deve ocorrer somente através das abstrações
    e fachadas arquiteturais definidas pelo Nucleus.

    Para a infraestrutura de persistência, a única fachada
    permitida é:

        nucleus.database.database

    Exemplo inválido:

        planets/user/repository.py

            from nucleus.database.drivers.driver_sqlalchemy import DriverSQLAlchemy

        source = "planets.user.repository"
        target = "nucleus.database.drivers.driver_sqlalchemy"

    Exemplo válido:

        planets/user/repository.py

            from nucleus.database.database import Database

        source = "planets.user.repository"
        target = "nucleus.database.database"

    A regra reconhece o Planet em ambos os layouts:

        planets.<planet>.*
        orbits.planets.<planet>.*
    """

    # Segmento que identifica a coleção de Planets.
    PLANETS_SEGMENT = "planets"

    # Pacote de infraestrutura do Nucleus protegido pela regra.
    INFRASTRUCTURE_PACKAGE = "nucleus.database"

    # Fachadas do Nucleus permitidas para os Planets.
    #
    # Tupla para poder receber uma fachada nova (storage, por
    # exemplo) sem mexer no resto da regra — é ela que alimenta a
    # mensagem de violação.
    ALLOWED_FACADES = (
        "nucleus.database.database",
    )

    def code(self) -> str:
        return rule_code(DEPENDENCY, 11)

    def description(self) -> str:
        return (
            "Planets não devem conhecer detalhes da "
            "infraestrutura do Nucleus."
        )

    def validate(self, dependency: Dependency) -> None:

        # Três filtros em AND: origem é Planet E destino é
        # infraestrutura E o destino não é uma das fachadas
        # liberadas.
        if not self._is_planet(dependency.source):
            return

        if not self._is_infrastructure(dependency.target):
            return

        # A exceção da regra: `nucleus.database.database` é a fachada,
        # e é justamente por onde o Planet DEVE passar.
        if self._is_allowed_facade(dependency.target):
            return

        raise SolarException(
            self._build_message(dependency)
        )

    def _is_planet(self, module: str) -> bool:

        return (
            self.PLANETS_SEGMENT
            in module.split(".")
        )

    def _is_infrastructure(self, target: str) -> bool:

        # Prefixo com ponto: todo `nucleus.database.*` é detalhe
        # interno — driver, ORM, model. Só a fachada escapa, e quem
        # libera é `_is_allowed_facade`.
        return (
            target == self.INFRASTRUCTURE_PACKAGE
            or target.startswith(
                f"{self.INFRASTRUCTURE_PACKAGE}."
            )
        )

    def _is_allowed_facade(self, target: str) -> bool:

        # Igualdade OU prefixo com ponto: importar de DENTRO do módulo
        # da fachada ainda é usar a fachada.
        for facade in self.ALLOWED_FACADES:

            if target == facade:
                return True

            if target.startswith(f"{facade}."):
                return True

        return False

    def _build_message(
        self,
        dependency: Dependency
    ) -> str:

        return (
            f"{self.code()}: "
            f"O Planet '{dependency.source}' não pode conhecer "
            f"o detalhe de infraestrutura '{dependency.target}'. "
            f"O acesso deve ocorrer somente através das fachadas "
            f"do Nucleus: {', '.join(self.ALLOWED_FACADES)}. "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )
