from datetime import datetime

from nucleus.middleware.error_handler import ErrorHandler
from observatory.records.error_log import ErrorLog


def _log(tmp_path, **kwargs) -> ErrorLog:

    return ErrorLog(path=tmp_path / "solar.sqlite", **kwargs)


# o erro e gravado com o codigo, a mensagem e a referencia da resposta
def test_records_the_payload_of_the_response(tmp_path):

    log = _log(tmp_path, solar_id="app-1", environment="dev")

    log.record(
        ValueError("algo falhou"),
        {
            "code": "INVALID_UPLOAD",
            "message": "genérica",
            "reference": "r1",
        }
    )

    entries = log.all()

    assert len(entries) == 1

    entry = entries[0]

    assert entry.number == 1
    assert entry.code == "INVALID_UPLOAD"
    assert entry.message == "genérica"
    assert entry.reference == "r1"
    assert entry.exception_type == "ValueError"
    assert "algo falhou" in entry.detail
    assert entry.solar_id == "app-1"
    assert entry.environment == "dev"


# o contexto da requisicao tambem vai para o registro
def test_records_the_request_context(tmp_path):

    log = _log(tmp_path)

    log.record(
        ValueError("x"),
        {"code": "X", "message": "m", "reference": "r"},
        {"method": "POST", "route": "/documents", "status": 500}
    )

    entry = log.all()[0]

    assert entry.method == "POST"
    assert entry.route == "/documents"
    assert entry.status == 500


# sem codigo na resposta o registro nao fica vazio
def test_missing_code_falls_back_to_unknown(tmp_path):

    log = _log(tmp_path)

    log.record(ValueError("x"))

    assert log.all()[0].code == "UNKNOWN"


# busca por referencia e contagem
def test_finds_by_reference_and_counts(tmp_path):

    log = _log(tmp_path)

    log.record(ValueError("a"), {"reference": "primeiro"})
    log.record(ValueError("b"), {"reference": "segundo"})

    assert log.count() == 2
    assert log.find("segundo").reference == "segundo"
    assert log.find("nao-existe") is None


# o ErrorHandler avisa o Observatorio ligado a ele
def test_handler_notifies_the_log(tmp_path):

    log = _log(tmp_path)

    payload = ErrorHandler(observers=[log]).handle(ValueError("falhou"))

    entry = log.find(payload["reference"])

    assert entry is not None
    assert entry.code == payload["code"]
    assert entry.exception_type == "ValueError"


# observador quebrado nao muda a resposta de erro
def test_broken_observer_does_not_change_the_response():

    def quebrado(error, payload, context):
        raise RuntimeError("observador fora do ar")

    payload = ErrorHandler(observers=[quebrado]).handle(ValueError("x"))

    assert payload["code"] == "INTERNAL_ERROR"
    assert payload["reference"]


# o momento segue o formato do Observatorio
def test_moment_follows_the_observatory_format(tmp_path):

    log = _log(tmp_path)

    log.record(ValueError("x"))

    moment = log.all()[0].moment

    assert len(moment) == len("2026-10-05 17:39:26")
    assert datetime.strptime(moment, "%Y-%m-%d %H:%M:%S")


# o relogio pode ser injetado
def test_clock_is_configurable(tmp_path):

    log = _log(tmp_path, clock=lambda: "2026-01-01 00:00:00")

    log.record(ValueError("x"))

    assert log.all()[0].moment == "2026-01-01 00:00:00"


# o banco e proprio do Observatorio, nao o da aplicacao
def test_creates_its_own_database_file(tmp_path):

    log = _log(tmp_path)

    log.record(ValueError("x"))

    assert (tmp_path / "solar.sqlite").is_file()
