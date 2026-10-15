# SOLAR-ARCH-002 — Repository não fala com o banco direto.
#
# O caminho é Repository -> Persistence -> Database. Quando o
# Repository importa a fachada, ele pula a camada de persistência e
# passa a decidir sozinho como o dado é lido e gravado.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import Rule


class RepositoryCannotDependOnDatabase(Rule):
    """
    Regra arquitetural:

    SOLAR-ARCH-002

    Um Repository não pode possuir uma dependência
    direta de Database.
    """

    def code(self) -> str:
        return "SOLAR-ARCH-002"

    def description(self) -> str:
        return (
            "Um Repository não pode possuir dependência "
            "direta de Database."
        )

    def validate(self, dependency: Dependency) -> None:

        # O contexto `Dependency` serve a ONZE regras do check do
        # mesmo nome: cada uma filtra a aresta de que trata. Esta só
        # reage a Repository -> Database — o resto passa direto.
        if not self._is_repository_to_database(dependency):
            return

        raise SolarException(
            self._build_message(dependency)
        )

    def _is_repository_to_database(
        self,
        dependency: Dependency
    ) -> bool:

        # `endswith(".repository")` e não a comparação com o caminho
        # exato de um módulo: pega TODO Repository, de qualquer
        # Planet, inclusive um que ainda não existe no projeto.
        source_is_repository = dependency.source.endswith(
            ".repository"
        )

        # Já o alvo é por IGUALDADE: só a fachada `Database` é
        # proibida. Um Repository pode depender de models, do
        # persistence e do ORM — o que ele não pode é falar com o
        # banco por conta própria.
        target_is_database = (
            dependency.target == "nucleus.database.database"
        )

        return source_is_repository and target_is_database

    def _build_message(
        self,
        dependency: Dependency
    ) -> str:

        return (
            f"{self.code()}: "
            f"Repository '{dependency.source}' não pode "
            f"possuir dependência direta de Database. "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )