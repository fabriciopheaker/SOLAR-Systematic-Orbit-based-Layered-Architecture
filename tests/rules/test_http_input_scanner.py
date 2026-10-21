"""
O que o scanner de entrada HTTP descreve.

A rota declara as DUAS coisas: para onde a requisicao vai e quem pode
entrar (`sanitizer=` e `validator=`). O scanner le a rota, e so ela.
"""

from nucleus.contracts.http_input import HttpInput
from nucleus.rules.scanner.http_input_scanner import HttpInputScanner


# A ROTA declara o essencial E os guardas.
ROUTE = """
documents_routes.add_url_rule(
    "/documents",
    "upload_document",
    DocumentController.upload,
    methods=["POST"],
    sanitizer=FileSanitizer,
    validator=FileValidator,
)
"""

# A mesma rota, SEM guarda declarada.
ROUTE_WITHOUT_GUARDS = """
documents_routes.add_url_rule(
    "/documents",
    "upload_document",
    DocumentController.upload,
    methods=["POST"],
)
"""

ROUTE_READ_ONLY = """
documents_routes.add_url_rule(
    "/documents",
    "list_documents",
    DocumentController.list,
    methods=["GET"],
)
"""

# Guarda declarado numa rota de LEITURA: quem declarou esta dizendo
# que por aqui passam dados, mesmo num metodo que nao leva corpo.
ROUTE_READ_ONLY_WITH_GUARDS = """
documents_routes.add_url_rule(
    "/documents",
    "list_documents",
    DocumentController.list,
    methods=["GET"],
    sanitizer=JsonSanitizer,
    validator=JsonValidator,
)
"""

ROUTE_MULTIPLE_METHODS = """
documents_routes.add_url_rule(
    "/documents",
    "documents",
    DocumentController.handle,
    methods=["GET", "POST"],
    sanitizer=FileSanitizer,
    validator=FileValidator,
)
"""

NO_ROUTES = """
from planets.user.controllers.user_controller import UserController

USERS = [UserController.list, UserController.show]
"""


def _scan(tmp_path, content: str) -> list[HttpInput]:
    """
    Varre um Planet com a rota dada.

    O arquivo mora em `planets/<p>/routes.py`: e o lugar onde a rota
    mora (SOLAR-ROF-004).
    """

    planet = tmp_path / "planets" / "documents"
    planet.mkdir(parents=True)

    (planet / "routes.py").write_text(content, encoding="utf-8")

    return HttpInputScanner(tmp_path).scan()


# o scanner le os guardas da PROPRIA rota
def test_scanner_reads_the_guards_from_the_route(tmp_path):

    http_input = _scan(tmp_path, ROUTE)[0]

    assert http_input.method == "POST"
    assert http_input.name == "/documents"
    assert http_input.sanitizer == "FileSanitizer"
    assert http_input.validator == "FileValidator"
    assert http_input.transports_data() is True


# a CLASSE ou a INSTANCIA: as duas declaram o mesmo guarda
def test_scanner_reads_the_guard_declared_as_instance(tmp_path):

    route = ROUTE.replace(
        "sanitizer=FileSanitizer",
        "sanitizer=FileSanitizer()"
    )

    assert _scan(tmp_path, route)[0].sanitizer == "FileSanitizer"


# rota sem guarda declarado: o scanner reporta None
def test_scanner_reports_missing_guards(tmp_path):

    http_input = _scan(tmp_path, ROUTE_WITHOUT_GUARDS)[0]

    assert http_input.sanitizer is None
    assert http_input.validator is None
    assert http_input.transports_data() is True


# METODO que aceita corpo ja caracteriza entrada de dados, mesmo sem
# guarda declarado (fecha a brecha de bypass)
def test_body_method_without_guard_still_transports_data(tmp_path):

    http_input = _scan(tmp_path, ROUTE_WITHOUT_GUARDS)[0]

    assert http_input.transports_data() is True


# guarda declarado JA E a rota dizendo "por aqui passam dados":
# a entrada transporta dados mesmo num metodo que nao leva corpo
def test_declared_guard_transports_data_in_a_read_method(tmp_path):

    http_input = _scan(tmp_path, ROUTE_READ_ONLY_WITH_GUARDS)[0]

    assert http_input.method == "GET"
    assert http_input.transports_data() is True


# entrada sem guarda e sem corpo nao transporta dados
def test_read_only_input_does_not_transport_data(tmp_path):

    http_input = _scan(tmp_path, ROUTE_READ_ONLY)[0]

    assert http_input.method == "GET"
    assert http_input.transports_data() is False


# cada metodo da rota e uma entrada HTTP distinta
def test_each_method_becomes_one_input(tmp_path):

    inputs = _scan(tmp_path, ROUTE_MULTIPLE_METHODS)

    assert sorted(http_input.method for http_input in inputs) == [
        "GET",
        "POST",
    ]


# arquivo sem rota nao produz entrada
def test_file_without_routes_produces_no_input(tmp_path):

    assert _scan(tmp_path, NO_ROUTES) == []
