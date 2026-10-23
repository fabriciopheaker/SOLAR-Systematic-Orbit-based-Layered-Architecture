import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.resources_must_not_expose_secrets import (
    ResourcesMustNotExposeSecrets
)
from nucleus.rules.scanner.resource_exposure import ResourceExposure


def _resource(fields: set[str]) -> ResourceExposure:

    return ResourceExposure(
        resource="UserResource",
        fields=frozenset(fields),
        file="planets/user/resources/user_resource.py",
        line=5
    )


# Resource que expoe password viola a regra
def test_resource_exposing_password_is_rejected():

    rule = ResourcesMustNotExposeSecrets()

    with pytest.raises(SolarException):
        rule.validate(_resource({"id", "name", "password"}))


# Resource que expoe password_hash viola a regra
def test_resource_exposing_password_hash_is_rejected():

    rule = ResourcesMustNotExposeSecrets()

    with pytest.raises(SolarException):
        rule.validate(_resource({"id", "password_hash"}))


# Resource que expoe secret_key viola a regra
def test_resource_exposing_secret_key_is_rejected():

    rule = ResourcesMustNotExposeSecrets()

    with pytest.raises(SolarException):
        rule.validate(_resource({"secret_key"}))


# Resource que expoe database_password viola a regra
def test_resource_exposing_database_password_is_rejected():

    rule = ResourcesMustNotExposeSecrets()

    with pytest.raises(SolarException):
        rule.validate(_resource({"database_password"}))


# Resource que expoe token interno viola a regra
def test_resource_exposing_internal_token_is_rejected():

    rule = ResourcesMustNotExposeSecrets()

    with pytest.raises(SolarException):
        rule.validate(_resource({"api_token", "refresh_token"}))


# Resource que expoe apenas dados publicos esta correto
def test_resource_without_secrets_is_allowed():

    rule = ResourcesMustNotExposeSecrets()

    rule.validate(_resource({"id", "name", "email", "created_at"}))


# Resource que nao expoe nada esta correto
def test_resource_without_fields_is_allowed():

    rule = ResourcesMustNotExposeSecrets()

    rule.validate(_resource(set()))
