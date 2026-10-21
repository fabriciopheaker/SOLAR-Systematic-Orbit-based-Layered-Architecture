import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.contracts.http_input import HttpInput
from nucleus.contracts.sanitizer import Sanitizer
from nucleus.contracts.validator import Validator
from nucleus.rules.architecture.http_input_must_pass_through_sanitization_and_validation import (
    HttpInputMustPassThroughSanitizationAndValidation
)
from nucleus.rules.architecture.planet_cannot_depend_on_planet import (
    PlanetCannotDependOnPlanet
)
from nucleus.rules.architecture.repository_cannot_depend_on_database import (
    RepositoryCannotDependOnDatabase
)
from nucleus.rules.rule_engine import RuleEngine
from nucleus.rules.scanner.dependency import Dependency
from nucleus.rules.scanner.http_input_scanner import HttpInputScanner
from nucleus.rules.scanner.route_scanner import RouteScanner


JSON = "application/json"
MULTIPART = "multipart/form-data"
FORM = "application/x-www-form-urlencoded"

COMPOSITION = """
from flask import Blueprint

from planets.auth.routes import auth_routes

api = Blueprint("api", __name__)

api.register_blueprint(auth_routes)
"""

# A rota declara o ESSENCIAL E os guardas: URL → Controller → método,
# com quem limpa e quem exige.
ROUTE_WITH_GUARDS = """
documents_routes.add_url_rule(
    "/documents",
    "upload_document",
    DocumentController.upload,
    methods=["POST"],
    sanitizer=FileSanitizer,
    validator=FileValidator,
)
"""

# A mesma rota, SEM guarda declarado: é o que a regra acusa.
ROUTE_WITHOUT_GUARDS = """
documents_routes.add_url_rule(
    "/documents",
    "upload_document",
    DocumentController.upload,
    methods=["POST"],
)
"""


def _planet(tmp_path, route: str):
    """
    Escreve um Planet com a rota dada.

    O arquivo mora em `planets/<p>/routes.py`: é o lugar onde a rota
    mora (SOLAR-ROF-004), e é de lá que o scanner lê os guardas.
    """

    planet = tmp_path / "planets" / "documents"
    planet.mkdir(parents=True)

    (planet / "routes.py").write_text(route, encoding="utf-8")

    return tmp_path


class JsonSanitizer(Sanitizer):

    def sanitize(self, payload):
        return payload


class JsonValidator(Validator):

    def validate(self, payload) -> None:
        return None


class FileSanitizer(Sanitizer):

    def sanitize(self, payload):
        return payload


class FileValidator(Validator):
    """
    Validações ESTRUTURAIS da entrada: arquivo enviado, tamanho,
    extensão, MIME type, quantidade, arquivo vazio.

    Nenhuma regra de NEGÓCIO do documento vive aqui.
    """

    def validate(self, payload) -> None:
        return None


class FormSanitizer(Sanitizer):

    def sanitize(self, payload):
        return payload


class FormValidator(Validator):

    def validate(self, payload) -> None:
        return None


def _rule() -> HttpInputMustPassThroughSanitizationAndValidation:

    return HttpInputMustPassThroughSanitizationAndValidation()


# 1. entrada HTTP JSON sem Sanitizer/Validator viola a regra
def test_json_input_without_guards_is_invalid():

    with pytest.raises(SolarException):
        _rule().validate(
            HttpInput(
                method="POST",
                name="/users",
                content_type=JSON
            )
        )


# sem Sanitizer e sem Validator, a regra aponta os dois
def test_json_input_without_each_guard_is_invalid():

    with pytest.raises(SolarException):
        _rule().validate(
            HttpInput(
                method="POST",
                name="/users",
                content_type=JSON,
                validator=JsonValidator()
            )
        )

    with pytest.raises(SolarException):
        _rule().validate(
            HttpInput(
                method="POST",
                name="/users",
                content_type=JSON,
                sanitizer=JsonSanitizer()
            )
        )


# 2. entrada HTTP JSON com Sanitizer e Validator respeita a regra
def test_json_input_with_guards_is_valid():

    _rule().validate(
        HttpInput(
            method="POST",
            name="/users",
            content_type=JSON,
            sanitizer=JsonSanitizer(),
            validator=JsonValidator()
        )
    )


# 3. entrada multipart/upload sem Sanitizer/Validator viola a regra
def test_multipart_input_without_guards_is_invalid():

    with pytest.raises(SolarException):
        _rule().validate(
            HttpInput(
                method="POST",
                name="/documents",
                content_type=MULTIPART
            )
        )


# 4. entrada multipart com FileSanitizer/FileValidator respeita
def test_multipart_input_with_file_guards_is_valid():

    _rule().validate(
        HttpInput(
            method="POST",
            name="/documents",
            content_type=MULTIPART,
            sanitizer=FileSanitizer(),
            validator=FileValidator()
        )
    )


# 5. a regra NAO exige JSON: form data tambem exige pipeline
def test_rule_does_not_require_json():

    form_input = HttpInput(
        method="POST",
        name="/login",
        content_type=FORM
    )

    with pytest.raises(SolarException):
        _rule().validate(form_input)

    _rule().validate(
        HttpInput(
            method="POST",
            name="/login",
            content_type=FORM,
            sanitizer=FormSanitizer(),
            validator=FormValidator()
        )
    )


# 6. a regra NAO e limitada ao metodo POST
def test_rule_is_not_limited_to_post():

    for method in ("PUT", "PATCH"):

        with pytest.raises(SolarException):
            _rule().validate(
                HttpInput(
                    method=method,
                    name="/users/1",
                    content_type=JSON
                )
            )

        _rule().validate(
            HttpInput(
                method=method,
                name="/users/1",
                content_type=JSON,
                sanitizer=JsonSanitizer(),
                validator=JsonValidator()
            )
        )


# entrada sem dados externos nao exige pipeline
def test_input_without_external_data_does_not_require_guards():

    _rule().validate(
        HttpInput(method="GET", name="/solar/health")
    )

    _rule().validate(
        HttpInput(method="GET", name="/users")
    )


# 7. o Validator de entrada nao e regra de negocio do UseCase:
# a regra exige apenas que um Validator EXISTA e nunca inspeciona
# o que ele valida. Validacoes estruturais bastam.
def test_validator_guards_the_input_not_the_business_rule():

    file_validator = FileValidator()

    _rule().validate(
        HttpInput(
            method="POST",
            name="/documents",
            content_type=MULTIPART,
            sanitizer=FileSanitizer(),
            validator=file_validator
        )
    )

    # A regra não conhece UseCase, Entity nem Repository de
    # negócio: ela apenas verifica a presença do pipeline.


# 8. composicao por register_blueprint nao e afetada pela regra
def test_blueprint_composition_is_not_affected(tmp_path):

    path = tmp_path / "routes.py"
    path.write_text(COMPOSITION, encoding="utf-8")

    # register_blueprint é COMPOSIÇÃO, não entrada HTTP:
    # o RouteScanner não produz declaração alguma.
    assert RouteScanner(tmp_path).scan() == []

    # E uma entrada sem dados externos não é exigida a ter pipeline.
    _rule().validate(
        HttpInput(method="GET", name="/solar/health")
    )


# 9. as regras de Dependency continuam funcionando exatamente como antes
def test_dependency_rules_are_unaffected():

    engine = RuleEngine([
        PlanetCannotDependOnPlanet(),
        RepositoryCannotDependOnDatabase(),
    ])

    dependency = Dependency(
        source="planets.user.repository",
        target="nucleus.database.database",
        file="planets/user/repository.py",
        line=3
    )

    with pytest.raises(SolarException):
        engine.validate(dependency)


# VALIDACAO ESTATICA: rota que transporta dados e NAO declara guarda
# nenhum e barrada no codigo-fonte.
def test_static_route_without_guards_violates_the_rule(tmp_path):

    root = _planet(tmp_path, ROUTE_WITHOUT_GUARDS)

    inputs = HttpInputScanner(root).scan()

    assert inputs

    for http_input in inputs:
        with pytest.raises(SolarException):
            _rule().validate(http_input)


# VALIDACAO ESTATICA: a rota declarando os guardas da entrada
# satisfaz a regra.
def test_static_route_with_guards_respects_the_rule(tmp_path):

    root = _planet(tmp_path, ROUTE_WITH_GUARDS)

    inputs = HttpInputScanner(root).scan()

    assert inputs

    for http_input in inputs:
        _rule().validate(http_input)


# BRECHA FECHADA: um POST sem guarda declarado continua sendo entrada
# de dados, e continua exigindo pipeline — mesmo sem `content_type`
# em lugar nenhum.
def test_static_post_without_content_type_still_requires_guards(
    tmp_path
):

    root = _planet(tmp_path, ROUTE_WITHOUT_GUARDS)

    inputs = HttpInputScanner(root).scan()

    assert inputs

    for http_input in inputs:

        assert http_input.transports_data() is True

        with pytest.raises(SolarException):
            _rule().validate(http_input)
