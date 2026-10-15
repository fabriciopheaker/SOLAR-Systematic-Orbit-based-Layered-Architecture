from nucleus.rules.scanner.mass_assignment_scanner import (
    MassAssignmentScanner
)


def _scan(tmp_path, content: str):

    path = tmp_path / "document_controller.py"
    path.write_text(content, encoding="utf-8")

    return MassAssignmentScanner(tmp_path).scan()


def _sources(tmp_path, content: str) -> list[str]:

    return [binding.source for binding in _scan(tmp_path, content)]


# ---------------------------------------------------------------------
# Expansao de dicionario
# ---------------------------------------------------------------------

def test_request_json_expansion_is_described(tmp_path):

    binding = _scan(
        tmp_path,
        "DocumentEntity(**request.json)\n"
    )[0]

    assert binding.target == "DocumentEntity"
    assert binding.source == "request.json"
    assert binding.kind == "expansion"


def test_expansion_into_model_is_described(tmp_path):

    binding = _scan(tmp_path, "DocumentModel(**payload)\n")[0]

    assert binding.target == "DocumentModel"
    assert binding.source == "payload"


def test_expansion_into_input_is_described(tmp_path):

    binding = _scan(tmp_path, "DocumentInput(**request.json)\n")[0]

    assert binding.target == "DocumentInput"


def test_orm_update_expansion_is_described(tmp_path):

    binding = _scan(
        tmp_path,
        "Model.query.filter_by(id=1).update(**request.json)\n"
    )[0]

    assert binding.target.startswith("Model.query")
    assert binding.source == "request.json"
    assert binding.kind == "update"


# ---------------------------------------------------------------------
# Construtor que recebe dicionario
# ---------------------------------------------------------------------

def test_from_dict_is_described(tmp_path):

    binding = _scan(
        tmp_path,
        "DocumentEntity.from_dict(request.json)\n"
    )[0]

    assert binding.target == "DocumentEntity"
    assert binding.source == "request.json"
    assert binding.kind == "mapping"


# ---------------------------------------------------------------------
# Preenchimento campo a campo
# ---------------------------------------------------------------------

def test_setattr_loop_is_described(tmp_path):

    content = (
        "for key, value in payload.items():\n"
        "    setattr(document, key, value)\n"
    )

    binding = _scan(tmp_path, content)[0]

    assert binding.target == "document"
    assert binding.source == "payload.items"
    assert binding.kind == "setattr"


# ---------------------------------------------------------------------
# Fronteiras
# ---------------------------------------------------------------------

# campos explicitos nao passam pelo scanner
def test_explicit_fields_are_not_described(tmp_path):

    content = (
        "document = DocumentEntity(\n"
        '    title=request.json["title"],\n'
        '    owner_id=request.json["owner_id"],\n'
        ")\n"
    )

    assert _scan(tmp_path, content) == []


# dicionario literal e descrito, mas com origem explicita
def test_dict_literal_source_is_described(tmp_path):

    content = 'DocumentEntity(**{"title": request.json["title"]})\n'

    binding = _scan(tmp_path, content)[0]

    assert binding.source == "{}"


# o Input que envelopa o request aparece como origem E o proprio
# request continua sendo descrito: o filtro esta no Input
def test_input_wrapping_request_yields_both_origins(tmp_path):

    content = "DocumentEntity(**DocumentInput(**request.json))\n"

    sources = _sources(tmp_path, content)

    assert "DocumentInput" in sources
    assert "request.json" in sources


# nome que nao e contrato nomeado nao interessa a esta regra
def test_plain_function_is_not_described(tmp_path):

    assert _scan(tmp_path, "send_email(**settings)\n") == []


def test_scanner_without_bindings_returns_empty(tmp_path):

    path = tmp_path / "service.py"
    path.write_text("VALUE = 1\n", encoding="utf-8")

    assert MassAssignmentScanner(tmp_path).scan() == []
