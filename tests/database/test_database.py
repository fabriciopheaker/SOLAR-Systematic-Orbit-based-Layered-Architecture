import sqlalchemy

from nucleus.database.database import Database
from nucleus.database.drivers.driver_sqlalchemy import DriverSQLAlchemy
from nucleus.exceptions.database_exception import DatabaseException


def test_database_exposes_orm_and_model():

    config = {
        "DB_CONNECTION": "sqlite",
        "DB_NAME": ":memory:",
        "DB_HOST": None,
        "DB_PORT": None,
        "DB_USER": None,
        "DB_PASS": None,
    }

    driver = DriverSQLAlchemy(config)

    Database.init(driver)

    from orbits.database.models.user_model import Users

    assert Database.orm is not None
    assert Database.model is sqlalchemy

    assert issubclass(Users, Database.orm)

    Database.close()


def test_build_connection_url_for_sqlite():

    driver = DriverSQLAlchemy({
        "DB_CONNECTION": "sqlite",
        "DB_NAME": ":memory:",
        "DB_HOST": None,
        "DB_PORT": None,
        "DB_USER": None,
        "DB_PASS": None,
    })

    assert driver._build_connection_url() == "sqlite+pysqlite:///:memory:"


def test_build_connection_url_for_postgres():

    driver = DriverSQLAlchemy({
        "DB_CONNECTION": "postgres",
        "DB_NAME": "sirius",
        "DB_HOST": "postgres",
        "DB_PORT": "5432",
        "DB_USER": "postgres",
        "DB_PASS": "postgres",
    })

    assert driver._build_connection_url() == (
        "postgresql+psycopg://postgres:postgres@postgres:5432/sirius"
    )


def test_build_connection_url_rejects_unsupported_connection():

    driver = DriverSQLAlchemy({
        "DB_CONNECTION": "oracle",
    })

    try:
        driver._build_connection_url()
    except DatabaseException as exception:
        assert exception.code == "INVALID_DATABASE_CONNECTION"
    else:
        raise AssertionError(
            "Esperava DatabaseException para conexão não suportada."
        )