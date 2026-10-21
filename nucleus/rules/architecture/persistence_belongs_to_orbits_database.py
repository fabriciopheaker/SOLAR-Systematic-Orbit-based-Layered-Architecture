# SOLAR-RED-007 — Persistence mora em `orbits.database.persistence`.
#
# A regra olha os DOIS lados da aresta: um módulo de persistência
# pode aparecer como quem importa ou como importado. Em
# `from planets.user.persistence import X`, a violação está no ALVO.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import DEPENDENCY, Rule, rule_code


class PersistenceBelongsToOrbitsDatabase(Rule):
    """
    Regra arquitetural:

    SOLAR-RED-007

    Persistence pertence à camada de Database de Orbits.

    Todo módulo da camada de Persistence deve estar
    localizado em:

        orbits.database.persistence

    Portanto, qualquer módulo de Persistence fora desse
    caminho é uma violação.

    Exemplo inválido:

        planets/user/persistence.py

        source = "planets.user.persistence"

    Exemplo inválido:

        from nucleus.database.persistence.persistence import Persistence

        target = "nucleus.database.persistence.persistence"

    Exemplo válido:

        from orbits.database.persistence.persistence import Persistence

        target = "orbits.database.persistence.persistence"

    Exemplo válido:

        from orbits.database.persistence.users.user_persistency import UserPersistency

        target = "orbits.database.persistence.users.user_persistency"
    """

    # Segmento que identifica a camada de Persistence.
    PERSISTENCE_SEGMENT = "persistence"

    # Local canônico da camada de Persistence na SOLAR.
    CANONICAL_PACKAGE = "orbits.database.persistence"

    def code(self) -> str:
        return rule_code(DEPENDENCY, 7)

    def description(self) -> str:
        return (
            "Persistence pertence à camada de Database "
            "de Orbits."
        )

    def validate(self, dependency: Dependency) -> None:

        for module in (
            dependency.source,
            dependency.target
        ):

            # Não é da camada: nada a ver com esta regra.
            if not self._is_persistence(module):
                continue

            # É da camada E está no lugar certo.
            if self._belongs_to_canonical(module):
                continue

            raise SolarException(
                self._build_message(dependency, module)
            )

    def _is_persistence(self, module: str) -> bool:

        # Segmento, e não substring: `user_persistency` (segmento
        # "persistency") NÃO conta como a camada — é isso que faz
        # `orbits/database/persistence/users/user_persistency.py`
        # não ser lido como "Persistence fora do lugar".
        return (
            self.PERSISTENCE_SEGMENT
            in module.split(".")
        )

    def _belongs_to_canonical(self, module: str) -> bool:

        # Ponto no `startswith` pelo mesmo motivo das outras regras de
        # caminho: `orbits.database.persistencez` não é a camada.
        return (
            module == self.CANONICAL_PACKAGE
            or module.startswith(
                f"{self.CANONICAL_PACKAGE}."
            )
        )

    def _build_message(
        self,
        dependency: Dependency,
        module: str
    ) -> str:

        return (
            f"{self.code()}: "
            f"Persistence '{module}' deve pertencer a "
            f"'{self.CANONICAL_PACKAGE}'. "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )
