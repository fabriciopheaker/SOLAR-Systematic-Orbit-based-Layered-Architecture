# SOLAR-RED-012 — comunicação externa mora nos Satellites.
#
# O Satellite é a FRONTEIRA: é o único que conhece `requests`,
# `httpx` e cia. Assim, trocar de biblioteca ou de provedor é mexer em
# um lugar só, e o Planet continua sem saber que existe rede.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import DEPENDENCY, Rule, rule_code


class ExternalCommunicationBelongsToSatellites(Rule):
    """
    Regra arquitetural:

    SOLAR-RED-012

    Satellites são a fronteira de comunicação externa
    e intermódulo.

    Direção permitida:

        Planet → Satellite → Planet / serviço externo

    Toda comunicação com serviços externos deve passar
    por um Satellite. Nenhum outro módulo deve conhecer
    diretamente bibliotecas de comunicação externa.

    Exemplo inválido:

        planets/user/service.py

            import requests

        source = "planets.user.service"
        target = "requests"

    Exemplo válido:

        satellites/auth/auth_satellite.py

            import requests

        source = "satellites.auth.auth_satellite"
        target = "requests"
    """

    # Pacote responsável pela comunicação externa
    # e intermódulo.
    SATELLITE_PACKAGE = "satellites"

    # Bibliotecas de comunicação externa que pertencem
    # exclusivamente aos Satellites.
    EXTERNAL_PACKAGES = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib3",
    )

    def code(self) -> str:
        return rule_code(DEPENDENCY, 12)

    def description(self) -> str:
        return (
            "Satellites são a fronteira de comunicação "
            "externa e intermódulo."
        )

    def validate(self, dependency: Dependency) -> None:

        # Origem E destino: qualquer módulo pode importar quase
        # qualquer coisa; o que se restringe são as bibliotecas de
        # comunicação externa. Quem pode conhecê-las é o Satellite —
        # é para isso que ele existe.
        if not self._is_external(dependency.target):
            return

        if self._is_satellite(dependency.source):
            return

        raise SolarException(
            self._build_message(dependency)
        )

    def _is_external(self, target: str) -> bool:

        # Igualdade OU prefixo com ponto, pacote a pacote: `requests`
        # e `requests.adapters` são a mesma biblioteca; `requests_x`
        # não é.
        for package in self.EXTERNAL_PACKAGES:

            if target == package:
                return True

            if target.startswith(f"{package}."):
                return True

        return False

    def _is_satellite(self, module: str) -> bool:

        # Prefixo com ponto: `satellites` e `satellites.*` são a
        # fronteira; `satellites_legacy` não é.
        return (
            module == self.SATELLITE_PACKAGE
            or module.startswith(
                f"{self.SATELLITE_PACKAGE}."
            )
        )

    def _build_message(
        self,
        dependency: Dependency
    ) -> str:

        return (
            f"{self.code()}: "
            f"O módulo '{dependency.source}' não pode acessar "
            f"o serviço externo '{dependency.target}' diretamente. "
            f"A comunicação deve passar por um Satellite "
            f"('{self.SATELLITE_PACKAGE}'). "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )
