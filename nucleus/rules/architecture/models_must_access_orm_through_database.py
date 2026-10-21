# SOLAR-RED-006 — Model chega ao ORM PELA fachada.
#
# Par da SOLAR-RED-005: a SOLAR-RED-005 proíbe o Model importar Persistence;
# esta proíbe importar ORM e Driver — os dois caminhos pelos quais o
# Model "aprende" a tecnologia por conta própria.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import DEPENDENCY, Rule, rule_code


class ModelsMustAccessOrmThroughDatabase(Rule):
    """
    Regra arquitetural:

    SOLAR-RED-006

    Models acessam a infraestrutura ORM através do Database.

    Direção permitida:

        Model → Database → ORM

    O Model NÃO deve conhecer diretamente a tecnologia de
    ORM nem o Driver. Todo acesso à infraestrutura deve
    passar pela fachada `nucleus.database.database`.

    Exemplo inválido:

        orbits/database/models/user_model.py

            import sqlalchemy

        source = "orbits.database.models.user_model"
        target = "sqlalchemy"

    Exemplo inválido:

        orbits/database/models/user_model.py

            from nucleus.database.drivers.driver_sqlalchemy import DriverSQLAlchemy

        source = "orbits.database.models.user_model"
        target = "nucleus.database.drivers.driver_sqlalchemy"

    Exemplo válido:

        orbits/database/models/user_model.py

            from nucleus.database.database import Database

        source = "orbits.database.models.user_model"
        target = "nucleus.database.database"

    A regra reconhece o Model tanto pelo segmento "models"
    no caminho do módulo quanto pelo sufixo do próprio
    módulo ("model" / "_model").
    """

    # Segmento que identifica a coleção de Models
    # dentro do caminho de um módulo.
    MODELS_SEGMENT = "models"

    # Fachada pela qual o ORM deve ser acessado.
    DATABASE_FACADE = "nucleus.database.database"

    # Pacote do Driver, que não deve ser conhecido pelo Model.
    DRIVER_PACKAGE = "nucleus.database.drivers"

    # Tecnologia de ORM que não deve ser conhecida pelo Model.
    ORM_PACKAGE = "sqlalchemy"

    def code(self) -> str:
        return rule_code(DEPENDENCY, 6)

    def description(self) -> str:
        return (
            "Models devem acessar a infraestrutura ORM "
            "através do Database."
        )

    def validate(self, dependency: Dependency) -> None:

        # Mesma estrutura das outras regras de aresta: origem é Model,
        # destino é infraestrutura DIRETA (ORM ou Driver). A fachada
        # `Database` não está em nenhuma das duas listas — e é
        # justamente por isso que ela passa.
        if not self._is_model(dependency.source):
            return

        if not self._is_direct_infrastructure(
            dependency.target
        ):
            return

        raise SolarException(
            self._build_message(dependency)
        )

    def _is_model(self, module: str) -> bool:

        parts = module.split(".")

        # Dois critérios, iguais aos da SOLAR-RED-005: o LUGAR
        # (segmento `models`) ou o NOME (`model` / `*_model`).
        if self.MODELS_SEGMENT in parts:
            return True

        last = parts[-1]

        return last == "model" or last.endswith("_model")

    def _is_direct_infrastructure(self, target: str) -> bool:

        # Dois alvos proibidos, e a fachada NÃO está entre eles — é
        # exatamente o que a regra exige. `_matches` evita repetir duas
        # vezes a mesma comparação de prefixo.
        return (
            self._matches(target, self.ORM_PACKAGE)
            or self._matches(target, self.DRIVER_PACKAGE)
        )

    def _matches(self, target: str, package: str) -> bool:

        # Igualdade OU prefixo COM PONTO: `sqlalchemy` e
        # `sqlalchemy.orm` são a mesma tecnologia; `sqlalchemyx` não.
        # O helper existe porque a comparação serve ao ORM e ao Driver.
        return (
            target == package
            or target.startswith(f"{package}.")
        )

    def _build_message(
        self,
        dependency: Dependency
    ) -> str:

        return (
            f"{self.code()}: "
            f"Model '{dependency.source}' não pode acessar "
            f"diretamente a infraestrutura '{dependency.target}'. "
            f"O acesso ao ORM deve passar por "
            f"'{self.DATABASE_FACADE}'. "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )
