"""
O que o `SolarBlueprint` acrescenta ao `Blueprint` do Flask.

O `add_url_rule` do Flask nao conhece `sanitizer=` nem `validator=`.
Este Blueprint existe para que a ROTA declare quem protege a entrada
dela — e para que o pipeline rode ANTES do Controller.
"""

from flask import Blueprint, Flask, g

import pytest

from nucleus.contracts.sanitizer import Sanitizer
from nucleus.contracts.validator import Validator
from nucleus.middleware.atmosphere import TREATED_DATA
from nucleus.middleware.solar_blueprint import SolarBlueprint


class SpySanitizer(Sanitizer):

    def __init__(self):
        self.calls: list = []

    def sanitize(self, payload) -> dict:
        self.calls.append("sanitize")
        return payload


class SpyValidator(Validator):

    def __init__(self):
        self.calls: list = []

    def validate(self, payload) -> None:
        self.calls.append("validate")


def _controller():
    return {"ok": True}, 200


def _reading_controller():
    return {"treated": getattr(g, TREATED_DATA)}, 200


def _app_with(guards: dict) -> Flask:

    app = Flask(__name__)

    blueprint = SolarBlueprint("planet", __name__)

    blueprint.add_url_rule(
        "/documents",
        "upload",
        _controller,
        methods=["POST"],
        **guards
    )

    app.register_blueprint(blueprint)

    return app


# o Blueprint do FLASK nao serve para declarar os guardas: ele ACEITA a
# declaracao e estoura no REGISTRO, porque os keywords vao parar no
# `Rule` do Werkzeug, que nao os conhece
def test_the_flask_blueprint_rejects_the_keywords_on_registration():

    app = Flask(__name__)

    blueprint = Blueprint("planet", __name__)

    blueprint.add_url_rule(
        "/documents",
        "upload",
        _controller,
        methods=["POST"],
        sanitizer=SpySanitizer,
        validator=SpyValidator,
    )

    with pytest.raises(TypeError):
        app.register_blueprint(blueprint)


# os guardas declarados na rota rodam ANTES do Controller
def test_the_declared_guards_run_before_the_controller():

    sanitizer = SpySanitizer()
    validator = SpyValidator()

    app = _app_with({
        "sanitizer": sanitizer,
        "validator": validator,
    })

    app.test_client().post("/documents", json={"a": 1})

    # VALIDAR antes de SANITIZAR: e a ordem do pipeline.
    assert validator.calls == ["validate"]
    assert sanitizer.calls == ["sanitize"]


# a CLASSE serve: quem declara a rota nao precisa instanciar
def test_the_guard_class_is_instantiated():

    app = _app_with({
        "sanitizer": SpySanitizer,
        "validator": SpyValidator,
    })

    response = app.test_client().post("/documents", json={"a": 1})

    # A requisicao NAO estoura: quem executou foi a INSTANCIA criada
    # pelo Blueprint, e nao a classe (que receberia o payload no lugar
    # do `self`).
    assert response.status_code == 200


# rota sem guarda declarado passa direto
def test_a_route_without_guards_passes_through():

    app = Flask(__name__)

    blueprint = SolarBlueprint("planet", __name__)

    blueprint.add_url_rule(
        "/health",
        "health",
        _controller,
        methods=["GET"],
    )

    app.register_blueprint(blueprint)

    assert app.test_client().get("/health").status_code == 200


# rota sem guarda recebe `{}` no `g`, e nao um AttributeError
def test_a_route_without_guards_gets_empty_treated_data():

    app = Flask(__name__)

    blueprint = SolarBlueprint("planet", __name__)

    blueprint.add_url_rule(
        "/leitura",
        "leitura",
        _reading_controller,
        methods=["GET"],
    )

    app.register_blueprint(blueprint)

    body = app.test_client().get("/leitura").get_json()

    assert body == {"treated": {}}
