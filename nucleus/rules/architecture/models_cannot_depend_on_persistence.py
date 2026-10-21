# SOLAR-RED-005 — Model não conhece Persistence.
#
# O Model é MAPEAMENTO; a Persistence é ACESSO A DADO. Juntar os dois
# é o começo do Model que sabe consultar — e a SOLAR-RED-006
# (Model -> Database -> ORM) fixa por onde o ORM chega.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import DEPENDENCY, Rule, rule_code


class ModelsCannotDependOnPersistence(Rule):
    """
    Regra arquitetural:

    SOLAR-RED-005

    Models não devem conhecer Persistence.

    O Model representa apenas o mapeamento da estrutura
    de dados no banco. O acesso a dados é responsabilidade
    da camada Persistence.

    Portanto, um Model NÃO pode possuir dependência
    direta de Persistence.

    Exemplo inválido:

        orbits/database/models/user_model.py

            from orbits.database.persistence.persistence import Persistence

        source = "orbits.database.models.user_model"
        target = "orbits.database.persistence.persistence"

    Direção permitida (SOLAR-RED-006):

        Model → Database → ORM

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

    # Pacote que concentra o acesso a dados.
    PERSISTENCE_PACKAGE = "orbits.database.persistence"

    def code(self) -> str:
        return rule_code(DEPENDENCY, 5)

    def description(self) -> str:
        return (
            "Models não devem possuir dependência "
            "direta de Persistence."
        )

    def validate(self, dependency: Dependency) -> None:

        # O Model descreve ESTRUTURA; quem acessa dado é a Persistence.
        # Um Model que importa Persistence passou a ter as duas
        # responsabilidades.
        if not self._is_model(dependency.source):
            return

        if not self._is_persistence(dependency.target):
            return

        raise SolarException(
            self._build_message(dependency)
        )

    def _is_model(self, module: str) -> bool:

        parts = module.split(".")

        # Critério 1: o módulo está dentro de um pacote `models` — e aí
        # TODA classe de lá conta, o que é coerente com a
        # SOLAR-ROF-007 (uma classe por arquivo em `models/`).
        if self.MODELS_SEGMENT in parts:
            return True

        # Critério 2: o próprio módulo se declara Model pelo nome
        # (`model` / `*_model`), onde quer que esteja.
        last = parts[-1]

        return last == "model" or last.endswith("_model")

    def _is_persistence(self, target: str) -> bool:

        # Prefixo COM PONTO: `orbits.database.persistence` e seus
        # filhos são a camada; `persistence_helpers` no mesmo nível
        # não é.
        return (
            target == self.PERSISTENCE_PACKAGE
            or target.startswith(
                f"{self.PERSISTENCE_PACKAGE}."
            )
        )

    def _build_message(
        self,
        dependency: Dependency
    ) -> str:

        return (
            f"{self.code()}: "
            f"Model '{dependency.source}' não pode possuir "
            f"dependência direta de Persistence "
            f"('{self.PERSISTENCE_PACKAGE}'). "
            f"O Model deve acessar a infraestrutura ORM "
            f"através do Database. "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )
