from nucleus.rules.scanner.error_exposure_scanner import (
    ErrorExposureScanner
)


def _scan(tmp_path, content: str):

    path = tmp_path / "application.py"
    path.write_text(content, encoding="utf-8")

    return ErrorExposureScanner(tmp_path).scan()


def _handler(body: str) -> str:
    """
    Monta um `except` que captura a exceção em uma variável.
    """

    return (
        "def handle():\n"
        "    try:\n"
        "        process()\n"
        "    except Exception as error:\n"
        f"{body}"
    )


# ---------------------------------------------------------------------
# Formas de renderizar o detalhe interno
# ---------------------------------------------------------------------

def test_str_of_exception_is_described(tmp_path):

    finding = _scan(
        tmp_path,
        _handler('        return {"error": str(error)}\n')
    )[0]

    assert finding.handler == "error"
    assert finding.detail == "str"
    assert finding.destination == "response"


def test_repr_of_exception_is_described(tmp_path):

    finding = _scan(
        tmp_path,
        _handler('        return {"error": repr(error)}\n')
    )[0]

    assert finding.detail == "repr"


def test_fstring_naming_the_exception_is_described(tmp_path):

    finding = _scan(
        tmp_path,
        _handler('        return {"erro": f"falhou: {error}"}\n')
    )[0]

    assert finding.detail == "f-string"
    assert finding.destination == "response"


def test_format_call_is_described(tmp_path):

    finding = _scan(
        tmp_path,
        _handler('        return {"erro": "{}".format(error)}\n')
    )[0]

    assert finding.detail == "format"


def test_exception_args_are_described(tmp_path):

    finding = _scan(
        tmp_path,
        _handler('        return {"erro": error.args}\n')
    )[0]

    assert finding.detail == "args"


def test_traceback_is_described(tmp_path):

    finding = _scan(
        tmp_path,
        _handler('        return {"tb": traceback.format_exc()}\n')
    )[0]

    assert finding.detail == "traceback"


# ---------------------------------------------------------------------
# Destino
# ---------------------------------------------------------------------

def test_log_destination_is_described(tmp_path):

    finding = _scan(
        tmp_path,
        _handler('        logger.error(f"falha: {error}")\n')
    )[0]

    assert finding.detail == "f-string"
    assert finding.destination == "log"


def test_raise_destination_is_response(tmp_path):

    finding = _scan(
        tmp_path,
        _handler('        raise ValueError(f"falhou: {error}")\n')
    )[0]

    assert finding.destination == "response"


def test_jsonify_destination_is_response(tmp_path):

    finding = _scan(
        tmp_path,
        _handler('        return jsonify({"erro": str(error)})\n')
    )[0]

    assert finding.destination == "response"


# o detalhe que vira REGISTRO (não resposta) não é acusado: passar
# perto de um `return` não basta, o detalhe tem que estar no valor
# retornado
# (foi o falso positivo que este próprio projeto produziu em
# rules/project_validator.py)
def test_recorded_detail_is_local(tmp_path):

    content = _handler(
        "        violacoes.append(Registro(mensagem=str(error)))\n"
        "        return violacoes\n"
    )

    finding = _scan(tmp_path, content)[0]

    assert finding.destination == "local"


# guardar o detalhe em uma variavel e retornar a variavel continua
# sendo vazamento
# (um nivel de indirecao)
def test_detail_returned_through_a_variable_is_response(tmp_path):

    content = (
        "def handle():\n"
        "    try:\n"
        "        process()\n"
        "    except Exception as error:\n"
        "        detalhe = str(error)\n"
        '        return {"error": detalhe}\n'
    )

    finding = _scan(tmp_path, content)[0]

    assert finding.destination == "response"


# retornar uma mensagem generica com o detalhe guardado tambem esta
# correto
def test_generic_response_with_stored_detail_is_allowed(tmp_path):

    content = (
        "def handle():\n"
        "    try:\n"
        "        process()\n"
        "    except Exception as error:\n"
        "        detalhe = str(error)\n"
        '        return {"error": "nao foi possivel processar"}\n'
    )

    assert _scan(tmp_path, content)[0].destination == "local"


# nome reaproveitado depois para uma mensagem generica NAO vira
# falso positivo: por isso o detalhe só é seguido por nome que
# recebe atribuição unica
def test_reused_variable_does_not_create_a_false_positive(tmp_path):

    content = (
        "def handle():\n"
        "    try:\n"
        "        process()\n"
        "    except Exception as error:\n"
        "        detalhe = str(error)\n"
        "        logger.error(detalhe)\n"
        '        detalhe = "nao foi possivel processar"\n'
        '        return {"error": detalhe}\n'
    )

    assert _scan(tmp_path, content)[0].destination == "local"


# ---------------------------------------------------------------------
# Fronteiras
# ---------------------------------------------------------------------

# `f"{str(error)}"` casaria duas vezes; vale o detalhe de FORA
def test_nested_detail_is_reported_once(tmp_path):

    findings = _scan(
        tmp_path,
        _handler('        return {"erro": f"{str(error)}"}\n')
    )

    assert len(findings) == 1
    assert findings[0].detail == "f-string"


# usar a excecao sem renderizar detalhe nao e vazamento
def test_plain_exception_use_is_not_reported(tmp_path):

    content = _handler(
        '        logger.exception("falha ao processar")\n'
        '        return {"error": "nao foi possivel processar"}\n'
    )

    assert _scan(tmp_path, content) == []


# handler sem variavel tambem nao tem o que vazar
def test_handler_without_variable_is_ignored(tmp_path):

    content = (
        "def handle():\n"
        "    try:\n"
        "        process()\n"
        "    except Exception:\n"
        '        return {"error": "falhou"}\n'
    )

    assert _scan(tmp_path, content) == []


def test_scanner_without_handlers_returns_empty(tmp_path):

    path = tmp_path / "application.py"
    path.write_text("VALUE = 1\n", encoding="utf-8")

    assert ErrorExposureScanner(tmp_path).scan() == []
