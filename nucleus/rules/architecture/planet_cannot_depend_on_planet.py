# SOLAR-RED-001 — Planet não importa Planet.
#
# Absorveu a SOLAR-RED-004 (que tratava do mesmo assunto por outro
# caminho). A comunicação entre Planets passa por Satellite — é o que
# mantém cada Planet substituível sem arrastar os vizinhos.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import DEPENDENCY, Rule, rule_code


class PlanetCannotDependOnPlanet(Rule):
    """
    Regra arquitetural:

    SOLAR-RED-001

    Um Planet não pode possuir uma dependência direta
    de outro Planet.

    A comunicação entre Planets deve passar pela camada
    intermediária de Satellites:

        Planet → Satellite → Planet

    Exemplo inválido:

        planets/user/service.py

            from planets.auth.repository import AuthRepository

        source = "planets.user.service"
        target = "planets.auth.repository"

    Exemplo válido:

        planets/user/service.py

            from satellites.auth.auth_satellite import AuthSatellite

        source = "planets.user.service"
        target = "satellites.auth.auth_satellite"

    A regra reconhece o Planet em ambos os layouts:

        planets.<planet>.*
        orbits.planets.<planet>.*

    Importar componentes do PRÓPRIO Planet continua
    permitido.
    """

    # Segmento que identifica a coleção de Planets
    # dentro do caminho de um módulo.
    PLANETS_SEGMENT = "planets"

    # Pacote responsável pela comunicação entre Planets
    # e com serviços externos.
    SATELLITE_PACKAGE = "satellites"

    def code(self) -> str:
        return rule_code(DEPENDENCY, 1)

    def description(self) -> str:
        return (
            "Um Planet não pode possuir dependência "
            "direta de outro Planet."
        )

    def validate(self, dependency: Dependency) -> None:

        # O NOME do Planet, e não o caminho: `planets.user.x` e
        # `orbits.planets.user.y` são o MESMO Planet, e
        # comparar caminhos acusaria o import do próprio Planet.
        source_planet = self._planet_name(dependency.source)
        target_planet = self._planet_name(dependency.target)

        # A dependência não envolve dois Planets.
        if source_planet is None or target_planet is None:
            return

        # Import dentro do próprio Planet é permitido — e é o caso mais
        # comum do dia a dia.
        if source_planet == target_planet:
            return

        raise SolarException(
            self._build_message(
                dependency,
                source_planet,
                target_planet
            )
        )

    def _planet_name(self, module: str) -> str | None:
        """
        Extrai o nome do Planet a partir de um módulo.

        Exemplos:

            planets.user.repository
                → "user"

            orbits.planets.user.user_repository
                → "user"

            satellites.auth.auth_satellite
                → None

        Retorna None quando o módulo não pertence
        a um Planet.
        """

        parts = module.split(".")

        if self.PLANETS_SEGMENT not in parts:
            return None

        # `index` (a PRIMEIRA ocorrência) e não uma posição fixa: é
        # assim que os dois layouts são reconhecidos pelo mesmo código.
        index = parts.index(self.PLANETS_SEGMENT)

        # O módulo termina no próprio segmento "planets",
        # sem identificar um Planet.
        if index + 1 >= len(parts):
            return None

        # O segmento imediatamente depois de "planets" é o nome.
        return parts[index + 1]

    def _build_message(
        self,
        dependency: Dependency,
        source_planet: str,
        target_planet: str
    ) -> str:

        return (
            f"{self.code()}: "
            f"Planet '{source_planet}' não pode possuir uma "
            f"dependência direta do Planet '{target_planet}'. "
            f"A comunicação deve passar por Satellites "
            f"('{self.SATELLITE_PACKAGE}'). "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )