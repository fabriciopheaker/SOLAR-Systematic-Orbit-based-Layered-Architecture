# SOLAR-RED-010 — só o Driver conhece a tecnologia de ORM.
#
# É a regra que sustenta a troca de tecnologia — e é por causa dela
# que `DatabaseDriver` expõe `orm()`/`model()`: se SQLAlchemy aparece
# só em `nucleus/database/drivers/`, trocar de ORM é trocar o driver.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import DEPENDENCY, Rule, rule_code


class OrmBelongsToDriver(Rule):
    """
    Regra arquitetural:

    SOLAR-RED-010

    O Driver é responsável pela implementação tecnológica
    da persistência.

    Direção permitida:

        Database → DriverSQLAlchemy → SQLAlchemy

    Somente o Driver pode conhecer a tecnologia de ORM.
    Qualquer outro módulo que dependa diretamente de
    SQLAlchemy está violando a regra.

    Exemplo inválido:

        orbits/database/persistence/persistence.py

            import sqlalchemy

        source = "orbits.database.persistence.persistence"
        target = "sqlalchemy"

    Exemplo válido:

        nucleus/database/drivers/driver_sqlalchemy.py

            import sqlalchemy

        source = "nucleus.database.drivers.driver_sqlalchemy"
        target = "sqlalchemy"
    """

    # Pacote do Driver, responsável pela tecnologia de ORM.
    DRIVER_PACKAGE = "nucleus.database.drivers"

    # Tecnologia de ORM que pertence ao Driver.
    ORM_PACKAGE = "sqlalchemy"

    def code(self) -> str:
        return rule_code(DEPENDENCY, 10)

    def description(self) -> str:
        return (
            "O Driver é responsável pela implementação "
            "tecnológica da persistência (ORM)."
        )

    def validate(self, dependency: Dependency) -> None:

        # Duas perguntas em sequência, na ordem que descarta mais
        # rápido: primeiro "isto é ORM?", depois "quem importa é o
        # Driver?".
        if not self._is_orm(dependency.target):
            return

        # Exceção única da regra: o Driver PODE — mais que isso,
        # DEVE — conhecer a tecnologia. É ele que a isola do resto
        # da aplicação.
        if self._is_driver(dependency.source):
            return

        raise SolarException(
            self._build_message(dependency)
        )

    def _is_orm(self, target: str) -> bool:

        # Igualdade OU prefixo COM PONTO: `sqlalchemy` e
        # `sqlalchemy.orm` são a mesma tecnologia; `sqlalchemyx` NÃO
        # é — e é o ponto no `startswith` que separa os dois casos.
        return (
            target == self.ORM_PACKAGE
            or target.startswith(f"{self.ORM_PACKAGE}.")
        )

    def _is_driver(self, module: str) -> bool:

        # Mesmo cuidado de `_is_orm`: sem o ponto, um pacote vizinho
        # de nome parecido passaria como Driver.
        return (
            module == self.DRIVER_PACKAGE
            or module.startswith(f"{self.DRIVER_PACKAGE}.")
        )

    def _build_message(
        self,
        dependency: Dependency
    ) -> str:

        return (
            f"{self.code()}: "
            f"O módulo '{dependency.source}' não pode conhecer "
            f"a tecnologia de ORM '{dependency.target}'. "
            f"Somente o Driver "
            f"('{self.DRIVER_PACKAGE}') é responsável pela "
            f"implementação tecnológica da persistência. "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )
