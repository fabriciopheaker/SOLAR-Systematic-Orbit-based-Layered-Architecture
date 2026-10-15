# SOLAR-ARCH-003 — Repository fala com Persistence.
#
# Fecha o caminho Repository -> Persistence -> Database. As regras 002,
# 005 e 009 cuidam de cada atalho proibido; esta cuida do atalho mais
# tentador de todos: ir direto no Model, que já está ali importável.
from nucleus.rules.scanner.dependency import Dependency
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import Rule


class RepositoryMustUsePersistence(Rule):
    """
    Regra arquitetural:

    SOLAR-ARCH-003

    Um Repository deve acessar dados através de Persistence.

    Fluxo permitido:

        Repository → Persistence → Database

    Portanto, um Repository NÃO pode possuir dependência
    direta de outro componente de acesso a dados
    (Database, Driver, ORM ou Models).

    Exemplo válido:

        planets/user/repository.py

            from orbits.database.persistence.persistence import Persistence

        source = "planets.user.repository"
        target = "orbits.database.persistence.persistence"

    Exemplo inválido:

        planets/user/repository.py

            from orbits.database.models.user_model import UserModel

        source = "planets.user.repository"
        target = "orbits.database.models.user_model"
    """

    # Pacote que concentra o acesso a dados permitido
    # para os Repositories.
    PERSISTENCE_PACKAGE = "orbits.database.persistence"

    # Camadas de acesso a dados que NÃO podem ser
    # acessadas diretamente por um Repository.
    DATA_LAYER_PACKAGES = (
        "nucleus.database",
        "orbits.database",
    )

    def code(self) -> str:
        return "SOLAR-ARCH-003"

    def description(self) -> str:
        return (
            "Um Repository deve acessar dados através de "
            "Persistence."
        )

    def validate(self, dependency: Dependency) -> None:

        # Três perguntas, e a do MEIO é a que libera: Repository que
        # importa Persistence passa. Só depois se pergunta se o destino
        # é camada de dados — assim uma dependência de `typing`, por
        # exemplo, morre no terceiro `if` sem ser acusada.
        if not self._is_repository(dependency):
            return

        if self._is_persistence(dependency.target):
            return

        if not self._is_data_layer(dependency.target):
            return

        raise SolarException(
            self._build_message(dependency)
        )

    def _is_repository(
        self,
        dependency: Dependency
    ) -> bool:

        # Último SEGMENTO do módulo, e não o caminho inteiro:
        # `repository` ou `*_repository` identificam a peça onde quer
        # que ela esteja.
        module = dependency.source.split(".")[-1]

        return (
            module == "repository"
            or module.endswith("_repository")
        )

    def _is_persistence(self, target: str) -> bool:

        return (
            target == self.PERSISTENCE_PACKAGE
            or target.startswith(
                f"{self.PERSISTENCE_PACKAGE}."
            )
        )

    def _is_data_layer(self, target: str) -> bool:

        # `startswith` com TUPLA: vale para qualquer uma das camadas de
        # dados listadas. A lista é mais larga que a proibição —
        # `orbits.database` inteiro entra —, e a exceção da Persistence
        # já foi tratada antes de chegar aqui.
        #
        # NOTA: diferente das outras regras deste grupo, aqui NÃO há o
        # ponto no fim do prefixo, então `nucleus.databasex` também
        # casaria. É inofensivo na prática, mas vale conhecer a
        # diferença antes de copiar este padrão para outra regra.
        return target.startswith(
            self.DATA_LAYER_PACKAGES
        )

    def _build_message(
        self,
        dependency: Dependency
    ) -> str:

        return (
            f"{self.code()}: "
            f"Repository '{dependency.source}' deve acessar "
            f"dados através de Persistence "
            f"('{self.PERSISTENCE_PACKAGE}'). "
            f"Dependência direta de '{dependency.target}' "
            f"não é permitida. "
            f"Arquivo: {dependency.file}. "
            f"Linha: {dependency.line}."
        )
