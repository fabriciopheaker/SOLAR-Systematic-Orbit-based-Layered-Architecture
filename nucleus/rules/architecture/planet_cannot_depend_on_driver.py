# SOLAR-ARCH-009 — o Planet não conhece o Driver.
#
# Par da SOLAR-ARCH-008, olhando o outro lado: a 008 trata dos Orbits
# em geral; esta trata especificamente dos Planets, que é onde o
# negócio mora.
#
# Caminho permitido: Planet -> Orbits.Database.Persistence ->
# Nucleus.Database -> Driver.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import Rule


class PlanetCannotDependOnDriver(Rule):
    """
    Regra arquitetural:

    SOLAR-ARCH-009

    O Driver não deve ser conhecido pelos módulos de
    negócio (Planets).

    Um Planet NÃO pode possuir dependência direta do
    Driver de persistência.

    Exemplo inválido:

        planets/user/repository.py

            from nucleus.database.drivers.driver_sqlalchemy import DriverSQLAlchemy

        source = "planets.user.repository"
        target = "nucleus.database.drivers.driver_sqlalchemy"

    A regra reconhece o Planet em ambos os layouts:

        planets.<planet>.*
        orbits.planets.<planet>.*
    """

    # Segmento que identifica a coleção de Planets.
    #
    # Só o SEGMENTO importa, e não a posição dele: é assim que a
    # regra reconhece os DOIS layouts — `planets.<p>.*` e
    # `orbits.planets.<p>.*`.
    PLANETS_SEGMENT = "planets"

    # Pacote do Driver, que não deve ser conhecido
    # pelos módulos de negócio.
    DRIVER_PACKAGE = "nucleus.database.drivers"

    def code(self) -> str:
        return "SOLAR-ARCH-009"

    def description(self) -> str:
        return (
            "O Driver não deve ser conhecido pelos módulos "
            "de negócio (Planets)."
        )

    def validate(self, dependency: Dependency) -> None:

        # Origem E destino: um Planet importando qualquer outra coisa
        # passa, e qualquer módulo importando o Driver passa. Só a
        # aresta entre os dois acusa.
        if not self._is_planet(dependency.source):
            return

        if not self._is_driver(dependency.target):
            return

        raise SolarException(
            self._build_message(dependency)
        )

    def _is_planet(self, module: str) -> bool:

        # Segmento, e não substring: `planets_legacy` não é a coleção
        # de Planets.
        return (
            self.PLANETS_SEGMENT
            in module.split(".")
        )

    def _is_driver(self, target: str) -> bool:

        # Igualdade OU prefixo COM PONTO — sem o ponto, um pacote
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
            f"O Planet '{dependency.source}' não pode "
            f"conhecer o Driver '{dependency.target}'. "
            f"O Driver não deve ser acessado pelos "
            f"módulos de negócio. "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )
