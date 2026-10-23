from nucleus.rules.scanner.resource_exposure_scanner import (
    ResourceExposureScanner
)


WITH_SECRET = """
from nucleus.contracts.resource import Resource


class UserResource(Resource):

    @classmethod
    def to_object(cls, data):
        return {
            "id": data["id"],
            "name": data["name"],
            "password": data["password"],
        }
"""

CLEAN = """
from nucleus.contracts.resource import Resource


class UserResource(Resource):

    @classmethod
    def to_object(cls, data):
        return {
            "id": data["id"],
            "name": data["name"],
        }
"""

BY_BASE = """
from nucleus.contracts.resource import Resource


class UserPresenter(Resource):

    @classmethod
    def to_object(cls, data):
        return {"token": data["token"]}
"""

NOT_A_RESOURCE = """
class UserService:

    def run(self, data):
        return {"password": data["password"]}
"""


def _scan(tmp_path, content: str):

    path = tmp_path / "user_resource.py"
    path.write_text(content, encoding="utf-8")

    return ResourceExposureScanner(tmp_path).scan()


def test_scanner_collects_exposed_fields(tmp_path):

    resources = _scan(tmp_path, WITH_SECRET)

    assert len(resources) == 1

    resource = resources[0]

    assert resource.resource == "UserResource"
    assert resource.fields == frozenset(
        {"id", "name", "password"}
    )


def test_scanner_collects_clean_fields(tmp_path):

    resource = _scan(tmp_path, CLEAN)[0]

    assert resource.fields == frozenset({"id", "name"})


# Resource reconhecido pela BASE, mesmo com outro nome de classe
def test_scanner_recognizes_resource_by_base(tmp_path):

    resource = _scan(tmp_path, BY_BASE)[0]

    assert resource.resource == "UserPresenter"
    assert resource.fields == frozenset({"token"})


# classe que nao e Resource nao e descrita
def test_scanner_ignores_non_resource_classes(tmp_path):

    assert _scan(tmp_path, NOT_A_RESOURCE) == []
