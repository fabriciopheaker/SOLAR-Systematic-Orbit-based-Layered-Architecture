# SOLAR-RED-008 — Orbits fala com a fachada, não com o Driver.
#
# A fachada `nucleus.database.database` é o único ponto por onde a
# infraestrutura de persistência pode ser alcançada de fora do
# Nucleus. É ela que permite trocar o driver sem tocar nos Orbits.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import DEPENDENCY, Rule, rule_code


class OrbitsMustUseDatabaseFacade(Rule):
    """
    Regra arquitetural:

    SOLAR-RED-008

    O Database do Nucleus é a fachada da infraestrutura
    de persistência.

    Direção permitida:

        Orbits → Nucleus.Database → Driver

    Os Orbits NÃO devem conhecer o Driver diretamente.
    Todo acesso à infraestrutura de persistência deve
    passar pela fachada `nucleus.database.database`.

    Exemplo inválido:

        orbits/database/persistence/persistence.py

            from nucleus.database.drivers.driver_sqlalchemy import DriverSQLAlchemy

        source = "orbits.database.persistence.persistence"
        target = "nucleus.database.drivers.driver_sqlalchemy"

    Exemplo válido:

        orbits/database/persistence/persistence.py

            from nucleus.database.database import Database

        source = "orbits.database.persistence.persistence"
        target = "nucleus.database.database"
    """

    # Prefixo que identifica os módulos de Orbits.
    ORBITS_PACKAGE = "orbits"

    # Fachada pela qual a infraestrutura deve ser acessada.
    #
    # Usada SÓ na mensagem: a regra NÃO verifica que a fachada foi
    # usada — ela acusa quem importa o Driver. A distinção importa
    # para não se esperar dela mais do que ela faz.
    DATABASE_FACADE = "nucleus.database.database"

    # Pacote do Driver, que não deve ser conhecido pelos Orbits.
    DRIVER_PACKAGE = "nucleus.database.drivers"

    def code(self) -> str:
        return rule_code(DEPENDENCY, 8)

    def description(self) -> str:
        return (
            "O Database do Nucleus é a fachada da "
            "infraestrutura de persistência."
        )

    def validate(self, dependency: Dependency) -> None:

        # Toda a árvore `orbits.*` está sujeita: Planet, Database e
        # Satellites. O Driver só pode ser conhecido pelo próprio
        # Nucleus.
        if not self._is_orbits(dependency.source):
            return

        if not self._is_driver(dependency.target):
            return

        raise SolarException(
            self._build_message(dependency)
        )

    def _is_orbits(self, module: str) -> bool:

        # Prefixo COM PONTO: `orbits` e `orbits.*` são Orbits;
        # `orbits_extra` não é. O ponto é o que separa os dois.
        return (
            module == self.ORBITS_PACKAGE
            or module.startswith(f"{self.ORBITS_PACKAGE}.")
        )

    def _is_driver(self, target: str) -> bool:

        # Mesmo cuidado: sem o ponto no `startswith`, um pacote
        # vizinho de nome parecido passaria como Driver.
        return (
            target == self.DRIVER_PACKAGE
            or target.startswith(f"{self.DRIVER_PACKAGE}.")
        )

    def _build_message(
        self,
        dependency: Dependency
    ) -> str:

        return (
            f"{self.code()}: "
            f"O módulo de Orbits '{dependency.source}' não pode "
            f"acessar o Driver '{dependency.target}' diretamente. "
            f"O acesso deve passar pela fachada "
            f"'{self.DATABASE_FACADE}'. "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )
