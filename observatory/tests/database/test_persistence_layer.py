"""
Contratos da camada de persistência.

O que se trava aqui é a separação de responsabilidades:

    Repository → Persistence do Model → Database → Driver

- o Repository não conhece ORM, Model nem Database;
- cada Model tem a sua própria Persistence;
- a Persistence encapsula o Model e devolve DADOS;
- a composição fica no Kernel, depois de `Database.init()`.
"""

import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from nucleus.database.database import Database
from nucleus.exceptions.database_exception import DatabaseException
from nucleus.kernel import Kernel


PROJECT_ROOT = Path(__file__).resolve().parents[3]

PERSISTENCE_FILE = (
    PROJECT_ROOT
    / "orbits"
    / "database"
    / "persistence"
    / "users"
    / "user_persistency.py"
)

PERSISTENCE_FACADE_FILE = (
    PROJECT_ROOT
    / "orbits"
    / "database"
    / "persistence"
    / "persistence.py"
)

REPOSITORY_FILE = (
    PROJECT_ROOT
    / "orbits"
    / "planets"
    / "example"
    / "repository"
    / "example_repository.py"
)

USE_CASE_FILE = (
    PROJECT_ROOT
    / "orbits"
    / "planets"
    / "example"
    / "usecases"
    / "create_user_usecase.py"
)

CONFIG = {
    "APP_ENV": "TEST",
    "DB_CONNECTION": "sqlite",
    "DB_NAME": ":memory:",
    "DB_HOST": None,
    "DB_PORT": None,
    "DB_USER": None,
    "DB_PASS": None,
    "CORS": None,
    "HOST": "127.0.0.1",
    "PORT": "5099",
}


def _kernel(tmp_path):
    """
    Aplicação montada de verdade, em sqlite de memória.

    O módulo dos Models só pode ser importado DEPOIS de `mount()`,
    porque `class Users(Database.orm)` exige a ORM publicada.
    """

    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=TEST\n", encoding="utf-8")

    kernel = Kernel(
        env_file=env_file,
        config=CONFIG,
        storage_root=tmp_path / "storage",
    )

    kernel.mount()

    return kernel


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _all_imports(path: Path) -> list[str]:
    """
    Todos os módulos importados, inclusive dentro de funções.
    """

    imported: list[str] = []

    for node in ast.walk(_tree(path)):

        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)

        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    return imported


def _module_level_imports(path: Path) -> list[str]:
    """
    Só os imports do topo do módulo.
    """

    imported: list[str] = []

    for node in _tree(path).body:

        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)

        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    return imported


# ---------------------------------------------------------------------
# Composição
# ---------------------------------------------------------------------

# cada camada exporta a instância pronta que a camada seguinte usa:
# Persistence → Repository → UseCase
def test_planet_modules_export_the_wired_instances(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        from orbits.database.persistence.users.user_persistency import (
            UserPersistency,
            user_persistency,
        )
        from orbits.planets.example.repository.example_repository import (
            ExampleRepository,
            example_repository,
        )
        from orbits.planets.example.usecases.create_user_usecase import (
            CreateUserUseCase,
            create_user_use_case,
        )

        assert isinstance(user_persistency, UserPersistency)

        # A Persistence guarda a FACHADA, não uma sessão: o recurso de
        # banco continua sendo resolvido a cada operação.
        assert user_persistency.database is Database

        assert isinstance(example_repository, ExampleRepository)
        assert example_repository.users is user_persistency

        assert isinstance(create_user_use_case, CreateUserUseCase)
        assert create_user_use_case.repository is example_repository

        # Quem está dentro de uma rota recebe a instância já montada.
        assert kernel.app.extensions["solar"] is kernel

    finally:
        kernel.shutdown()


# o UseCase depende do Repository, e não de Persistence/Database
# (ele nem importa a camada de dados)
def test_use_case_depends_on_the_repository_not_on_persistence():

    imports = _all_imports(USE_CASE_FILE)

    for module in imports:

        assert not module.startswith(
            "orbits.database.persistence"
        ), f"UseCase não pode importar '{module}'."

        assert not module.startswith(
            "nucleus.database"
        ), f"UseCase não pode importar '{module}'."

    source = USE_CASE_FILE.read_text(encoding="utf-8")

    assert "CreateUserUseCase(self.repository)" not in source
    assert "ExampleRepository(" not in source


# encerrar a montagem fecha o banco
# (a Persistence dos Planets não guarda sessão para descartar)
def test_shutdown_closes_the_database(tmp_path):

    kernel = _kernel(tmp_path)

    kernel.shutdown()

    with pytest.raises(DatabaseException) as caught:
        Database.driver()

    assert caught.value.code == "DATABASE_NOT_INITIALIZED"


# ---------------------------------------------------------------------
# Persistence — DAO
# ---------------------------------------------------------------------

# a Persistence do Model devolve o CONTRATO de saída, nunca o objeto
# da ORM
# (a entidade de domínio tem nomes diferentes das colunas do Model)
def test_user_persistency_returns_the_output_contract(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        from orbits.database.persistence.users.output.create_user_output import (  # noqa: E501
            CreateUserOutput,
        )
        from orbits.database.persistence.users.user_persistency import (
            UserPersistency,
        )

        persistence = UserPersistency(Database)

        entity = SimpleNamespace(
            nome="Ana",
            email="ana@exemplo.com",
            senha_hash="hash",
        )

        saved = persistence.create(entity)

        assert isinstance(saved, CreateUserOutput)
        assert saved.id > 0
        assert saved.nome == "Ana"
        assert saved.email == "ana@exemplo.com"
        assert isinstance(saved.created_at, datetime)

        # O contrato público não expõe os nomes das colunas do Model.
        assert not hasattr(saved, "id_user")
        assert not hasattr(saved, "name_user")

        assert persistence.email_exists("ana@exemplo.com") is True
        assert persistence.email_exists("outra@exemplo.com") is False

    finally:
        kernel.shutdown()


# falha no commit não deixa a sessão pendente: a Persistence faz rollback
def test_user_persistency_rolls_back_when_the_commit_fails(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        from orbits.database.persistence.users.user_persistency import (
            UserPersistency,
        )

        class FakeSession:

            def __init__(self):
                self.rolled_back = False

            def add(self, user):
                return None

            def commit(self):
                raise RuntimeError("falha simulada no commit")

            def rollback(self):
                self.rolled_back = True

        class FakeDatabase:

            session_instance = FakeSession()

            @classmethod
            def session(cls):
                return cls.session_instance

        persistence = UserPersistency(FakeDatabase)

        entity = SimpleNamespace(
            nome="Ana",
            email="ana@exemplo.com",
            senha_hash="hash",
        )

        with pytest.raises(RuntimeError):

            persistence.create(entity)

        assert FakeDatabase.session_instance.rolled_back is True

    finally:
        kernel.shutdown()

# não existe registry genérico de persistências: cada Repository recebe
# a Persistence específica do Model que usa
def test_there_is_no_generic_persistence_registry():

    assert not (
        PROJECT_ROOT
        / "orbits"
        / "database"
        / "persistence"
        / "persistence.py"
    ).exists()


# O DAO importa o Model de forma EXPLÍCITA, no topo — sem import
# local para esconder a dependência arquitetural
def test_the_dao_declares_its_model_dependency_at_module_level():

    all_imports = [
        module for module in _all_imports(PERSISTENCE_FILE)
        if module == "orbits.database.models.user_model"
    ]

    module_imports = [
        module for module in _module_level_imports(PERSISTENCE_FILE)
        if module == "orbits.database.models.user_model"
    ]

    assert module_imports == ["orbits.database.models.user_model"]
    assert all_imports == module_imports


# a Persistence usa a sessão da fachada e não cria engine/sessão
def test_the_dao_uses_the_database_session():

    source = PERSISTENCE_FILE.read_text(encoding="utf-8")

    assert "self.database.session()" in source
    assert "create_engine" not in source
    assert "sessionmaker" not in source

    assert "sqlalchemy" not in _all_imports(PERSISTENCE_FILE)


# ---------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------

# o Repository conversa com a Persistence do Model e devolve o
# contrato dela SEM refazer a conversão
def test_repository_uses_only_the_model_persistence():

    calls: list[tuple] = []

    from orbits.database.persistence.users.output.create_user_output import (  # noqa: E501
        CreateUserOutput,
    )

    class FakeUserPersistence:

        def email_exists(self, email: str) -> bool:
            calls.append(("email_exists", email))
            return True

        def create(self, entity):
            calls.append(
                ("create", entity.nome, entity.email, entity.senha_hash)
            )

            output = CreateUserOutput(
                id=7,
                nome=entity.nome,
                email=entity.email,
                created_at=datetime.now(),
            )

            return output

    from orbits.planets.example.repository.example_repository import (
        ExampleRepository,
    )

    repository = ExampleRepository(FakeUserPersistence())

    entity = SimpleNamespace(
        nome="Ana",
        email="ana@exemplo.com",
        senha_hash="hash",
    )

    assert repository.email_taken("ana@exemplo.com") is True

    saved = repository.create(entity)

    assert isinstance(saved, CreateUserOutput)
    assert saved.id == 7
    assert saved.nome == "Ana"
    assert saved.email == "ana@exemplo.com"
    assert isinstance(saved.created_at, datetime)

    assert calls == [
        ("email_exists", "ana@exemplo.com"),
        ("create", "Ana", "ana@exemplo.com", "hash"),
    ]


# o Repository não importa Database, driver, Models nem SQLAlchemy
def test_repository_does_not_depend_on_infrastructure():

    forbidden = (
        "sqlalchemy",
        "nucleus.database",
        "orbits.database.models",
    )

    for module in _all_imports(REPOSITORY_FILE):

        assert not module.startswith(forbidden), (
            f"Repository não pode importar '{module}'."
        )


# o UseCase não compõe Database nem constrói Persistence
def test_use_case_does_not_compose_the_database():

    imports = _all_imports(USE_CASE_FILE)

    assert "nucleus.database.database" not in imports

    source = USE_CASE_FILE.read_text(encoding="utf-8")

    assert "Persistence(Database)" not in source
    assert "UserPersistency" not in source


# ---------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------

# nenhum módulo de negócio seleciona o driver: só o Kernel o faz
def test_only_the_kernel_imports_the_concrete_driver():

    offenders: list[str] = []

    for path in (PROJECT_ROOT / "orbits").rglob("*.py"):

        for module in _all_imports(path):

            if module.startswith("nucleus.database.drivers"):

                offenders.append(str(path.relative_to(PROJECT_ROOT)))

    assert offenders == []
