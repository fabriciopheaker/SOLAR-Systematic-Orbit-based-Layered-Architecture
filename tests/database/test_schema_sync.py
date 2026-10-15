"""
A montagem do esquema: o banco inicia montado.

O que se prova aqui e o que o KERNEL deixou de saber: os Models sao
achados pelo PACOTE, e o esquema se monta na inicializacao do banco,
sem a montagem da aplicacao pedir nada.
"""

import pytest

from nucleus.database.database import Database
from nucleus.exceptions.database_exception import DatabaseException
from nucleus.kernel import Kernel


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
    Aplicacao montada de verdade, em sqlite de memoria.

    A montagem e o estado que a descoberta exige: os Models sao
    importados por ela, e `class Users(Database.orm)` precisa da ORM
    ja publicada.
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


def _engine():
    """
    O engine do banco montado.
    """

    return Database.driver().engine


def _tables():
    """
    As tabelas que o BANCO tem — e nao as que o Model declara.

    Usa o modulo sqlalchemy publicado pela FACHADA (`Database.model`),
    e nao um import direto: e por ali que o projeto alcanca a ORM
    (SOLAR-ARCH-010).
    """

    return Database.model.inspect(_engine()).get_table_names()


def _columns_of(table):
    """
    As colunas que o BANCO tem.
    """

    return [
        column["name"]
        for column in Database.model.inspect(_engine()).get_columns(table)
    ]


# quem sobe a aplicacao nao pede nada: o banco inicia MONTADO
def test_the_bank_is_mounted_when_it_starts(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        assert "users" in _tables()

    finally:
        kernel.shutdown()


# o botao: desligado, o banco conecta e NAO mexe no esquema
def test_the_mount_can_be_turned_off(tmp_path, monkeypatch):

    monkeypatch.setattr(Database, "SYNC_ON_START", False)

    kernel = _kernel(tmp_path)

    try:
        assert _tables() == []

    finally:
        kernel.shutdown()


# a descoberta acha os Models pelo PACOTE, sem ninguem nomear nenhum
def test_the_models_are_found_by_the_package(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        assert "orbits.database.models.user_model" in Database._import_models()

    finally:
        kernel.shutdown()


# a descoberta e ORDENADA: o mesmo resultado em qualquer maquina,
# porque `iter_modules` devolve na ordem do sistema de arquivos
def test_the_models_are_imported_in_order(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        imported = Database._import_models()

        assert imported == sorted(imported)

    finally:
        kernel.shutdown()


# montar de novo nao estoura nem apaga nada: e o que permite rodar
# em toda subida
def test_mounting_again_changes_nothing(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        Database.sync()
        Database.sync()

    finally:
        kernel.shutdown()


# antes da inicializacao a recusa e explicita, em vez de um TypeError
# obscuro no meio de um modulo de Model
def test_sync_refuses_before_the_bank_is_initialized():

    # O `Database` e global: o teste garante o estado que quer
    # testar, em vez de depender da ordem em que os testes rodam.
    Database.close()

    with pytest.raises(DatabaseException) as caught:
        Database.sync()

    assert caught.value.code == "DATABASE_NOT_INITIALIZED"


# a coluna que o banco PERDEU volta: e o ALTER, e nao so o CREATE da
# tabela que faltava
#
# A coluna e a mais simples do Model, de proposito: em sqlite o DROP
# COLUMN nao aceita coluna presa a constraint ou indice.
def test_a_lost_column_comes_back(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        with _engine().begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE users DROP COLUMN data_deleted_user"
            )

        assert "data_deleted_user" not in _columns_of("users")

        Database.sync()

        assert "data_deleted_user" in _columns_of("users")

    finally:
        kernel.shutdown()


# a coluna que saiu do Model TAMBEM sai do banco: e o padrao. Esquema
# que so cresce acumula estrutura que ninguem mais declara.
def test_a_column_that_left_the_model_leaves_the_bank(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        with _engine().begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN coluna_antiga VARCHAR(10)"
            )

        Database.sync()

        assert "coluna_antiga" not in _columns_of("users")

    finally:
        kernel.shutdown()


# e `prune=False` preserva o que sobrou, para quem quiser so aditivo
def test_prune_false_keeps_what_left_the_model(tmp_path):

    kernel = _kernel(tmp_path)

    try:
        with _engine().begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN coluna_antiga VARCHAR(10)"
            )

        Database.sync(prune=False)

        assert "coluna_antiga" in _columns_of("users")

    finally:
        kernel.shutdown()
