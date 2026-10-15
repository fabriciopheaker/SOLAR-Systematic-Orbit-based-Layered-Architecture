import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.persistence_must_not_build_unsafe_sql import (
    PersistenceMustNotBuildUnsafeSql
)
from nucleus.rules.scanner.unsafe_sql import UnsafeSql


def _unsafe(
    module: str,
    kind: str = "concatenation"
) -> UnsafeSql:

    return UnsafeSql(
        module=module,
        kind=kind,
        file=module.replace(".", "/") + ".py",
        line=10
    )


# SQL inseguro na Persistence viola a regra
def test_unsafe_sql_in_persistence_is_rejected():

    rule = PersistenceMustNotBuildUnsafeSql()

    with pytest.raises(SolarException):
        rule.validate(
            _unsafe("orbits.database.persistence.persistence")
        )


# todas as formas de interpolar sao barradas
@pytest.mark.parametrize(
    "kind",
    ["concatenation", "f-string", "percent", "format"]
)
def test_all_interpolation_forms_are_rejected(kind):

    rule = PersistenceMustNotBuildUnsafeSql()

    with pytest.raises(SolarException):
        rule.validate(
            _unsafe(
                "orbits.database.persistence.users.user_persistency",
                kind
            )
        )


# SQL inseguro FORA da persistence nao e escopo desta regra
def test_unsafe_sql_outside_persistence_is_not_scoped():

    rule = PersistenceMustNotBuildUnsafeSql()

    rule.validate(_unsafe("planets.user.repository"))
