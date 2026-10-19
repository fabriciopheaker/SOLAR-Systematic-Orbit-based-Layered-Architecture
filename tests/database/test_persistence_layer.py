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


PROJECT_ROOT = Path(__file__).resolve().parents[2]

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

# o Kernel monta a Persistence depois do banco, e a deixa à disposição
def test_kernel_composes_the_persistence_layer(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        from orbits.database.persistence.persistence import Persistence
        from orbits.database.persistence.users.user_persistency import (
            UserPersistency,
        )

        assert isinstance(kernel.persistence, Persistence)
        assert isinstance(
            kernel.persistence.users(),
            UserPersistency
        )

        # Quem está dentro de uma rota recebe a instância já montada.
        assert kernel.app.extensions["solar"] is kernel

    finally:
        kernel.shutdown()


# o UseCase recebe a Persistence; ele não conhece Database nem driver
def test_use_case_receives_the_composed_persistence(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        from orbits.planets.example.repository.example_repository import (
            ExampleRepository,
        )
        from orbits.planets.example.usecases.create_user_usecase import (
            create_user_use_case,
        )

        use_case = create_user_use_case(kernel.persistence)

        assert isinstance(use_case.repository, ExampleRepository)

        # O Repository usa a Persistence DO MODEL — não a fachada
        # do banco nem uma persistência central.
        assert use_case.repository.users is kernel.persistence.users()

    finally:
        kernel.shutdown()


# encerrar a montagem descarta a Persistence junto com o banco
def test_shutdown_discards_the_persistence(tmp_path):

    kernel = _kernel(tmp_path)

    kernel.shutdown()

    assert kernel.persistence is None

    with pytest.raises(DatabaseException) as caught:
        Database.driver()

    assert caught.value.code == "DATABASE_NOT_INITIALIZED"


# ---------------------------------------------------------------------
# Persistence — DAO
# ---------------------------------------------------------------------

# a Persistence do Model devolve DADOS, nunca o objeto da ORM
def test_user_persistency_returns_plain_data(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        from orbits.database.persistence.users.user_persistency import (
            UserPersistency,
        )

        persistence = UserPersistency(Database)

        saved = persistence.create(
            name="Ana",
            email="ana@exemplo.com",
            password_hash="hash",
        )

        assert set(saved) == {
            "id",
            "nome",
            "email",
            "created_at",
        }

        assert saved["id"] > 0
        assert saved["nome"] == "Ana"
        assert saved["email"] == "ana@exemplo.com"
        assert isinstance(saved["created_at"], datetime)

        # Um dicionário não expõe os nomes das colunas do Model.
        assert not hasattr(saved, "id_user")

        assert persistence.email_exists("ana@exemplo.com") is True
        assert persistence.email_exists("outra@exemplo.com") is False

    finally:
        kernel.shutdown()


# a fachada Persistence só entrega a Persistence do Model; ela NÃO
# implementa as operações de acesso a dados
def test_persistence_facade_does_not_implement_dao_operations(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        from orbits.database.persistence.persistence import Persistence

        for operation in ("create", "email_exists", "delete", "find"):

            assert not hasattr(Persistence, operation)

    finally:
        kernel.shutdown()


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

# o Repository conversa com a Persistence do Model e devolve dados
def test_repository_uses_only_the_model_persistence():

    calls: list[tuple] = []

    class FakeUserPersistence:

        def email_exists(self, email: str) -> bool:
            calls.append(("email_exists", email))
            return True

        def create(self, *, name, email, password_hash):
            calls.append(("create", name, email, password_hash))

            return {
                "id": 7,
                "nome": name,
                "email": email,
                "created_at": datetime.now(),
            }

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

    assert saved["id"] == 7
    assert saved["nome"] == "Ana"
    assert saved["email"] == "ana@exemplo.com"
    assert isinstance(saved["created_at"], datetime)

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
