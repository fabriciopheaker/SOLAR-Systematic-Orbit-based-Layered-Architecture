import ast
from pathlib import Path

import pytest
from flask import Flask

from nucleus import kernel as kernel_module
from nucleus.broadcast.broadcast import Broadcast
from nucleus.broadcast.event import Event
from nucleus.database.database import Database
from nucleus.exceptions.validation_exception import ValidationException
from nucleus.kernel import Kernel
from nucleus.storage.storage import Storage


CONFIG = {
    "APP_ENV": "TEST",
    "DB_CONNECTION": "sqlite",
    "DB_NAME": ":memory:",
    "DB_HOST": None,
    "DB_PORT": None,
    "DB_USER": None,
    "DB_PASS": None,
    "CORS": None,
    "HOST": "127.0.0.1",
    "PORT": "5099",
}


def _env_file(tmp_path):
    """
    Arquivo de ambiente da aplicação, isolado por teste.
    """

    path = tmp_path / ".env"
    path.write_text("APP_ENV=TEST\n", encoding="utf-8")

    return path


@pytest.fixture
def kernel(tmp_path):

    instance = Kernel(
        env_file=_env_file(tmp_path),
        config=CONFIG,
        storage_root=tmp_path / "storage",
    )

    instance.mount()

    yield instance

    instance.shutdown()


# o Kernel usa a configuracao que recebeu, sem reler o ambiente
def test_mount_keeps_the_received_configuration(kernel):

    assert kernel.config["APP_ENV"] == "TEST"


# a identidade da aplicacao existe depois de montar
def test_mount_creates_the_identity(kernel):

    assert kernel.identity.secret_key
    assert kernel.identity.solar_id


# a identidade fica gravada no arquivo de ambiente
def test_identity_is_persisted_in_the_environment_file(tmp_path):

    env_file = _env_file(tmp_path)

    instance = Kernel(
        env_file=env_file,
        config=CONFIG,
        storage_root=tmp_path / "storage",
    )

    instance.mount()

    try:
        assert "SOLAR_ID=" in env_file.read_text(encoding="utf-8")

    finally:
        instance.shutdown()


# as tres fachadas ficam ligadas, e funcionando
def test_mount_starts_the_three_facades(kernel):

    assert Database.driver() is not None

    Storage.save("exemplo.txt", b"conteudo")

    assert Storage.read("exemplo.txt") == b"conteudo"

    Broadcast.publish(Event(name="teste", data={"chave": "valor"}))


# mount devolve a aplicacao web pronta
def test_mount_returns_the_application(kernel):

    assert isinstance(kernel.app, Flask)


# a rota de saude responde pela cadeia inteira
def test_health_route_answers(kernel):

    response = kernel.app.test_client().get("/solar/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "message": "bem-vindo",
        "application": "",
    }


# toda resposta leva os cabecalhos obrigatorios
def test_every_response_carries_the_security_headers(kernel):

    response = kernel.app.test_client().get("/solar/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


# erro vira resposta segura, com o codigo HTTP certo
def test_error_becomes_a_safe_response(kernel):

    app = kernel.app

    @app.route("/boom")
    def boom():
        raise ValidationException(
            "campo 'nome' ausente",
            code="INVALID_NAME"
        )

    response = app.test_client().get("/boom")
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["code"] == "INVALID_NAME"
    assert payload["reference"]

    # o detalhe interno nao atravessa a fronteira
    assert "ausente" not in payload["message"]


# o observador ligado ao Kernel recebe o erro tratado
def test_observers_receive_the_error(kernel):

    recebidos: list = []

    kernel.observe(
        lambda error, payload, context: recebidos.append(payload)
    )

    app = kernel.app

    @app.route("/boom")
    def boom():
        raise ValidationException("x", code="INVALID_X")

    app.test_client().get("/boom")

    assert len(recebidos) == 1
    assert recebidos[0]["code"] == "INVALID_X"


# erro sem codigo proprio cai no generico, com 500
def test_unexpected_error_is_internal(kernel):

    app = kernel.app

    @app.route("/explode")
    def explode():
        raise RuntimeError("falha inesperada")

    response = app.test_client().get("/explode")

    assert response.status_code == 500
    assert response.get_json()["code"] == "INTERNAL_ERROR"


# o Kernel NAO nomeia Model nenhum: quem descobre os Models e o
# `schema` de Orbits, a partir do PACOTE. Sem esta separacao, cada
# Model novo viraria uma linha a mais na montagem -- e a montagem
# passaria a conhecer conteudo de Orbits.
#
# Lido por AST, e nao por busca de texto: o que se proibe e IMPORTAR,
# nao mencionar.
def test_the_kernel_does_not_name_any_model():

    tree = ast.parse(
        Path(kernel_module.__file__).read_text(encoding="utf-8")
    )

    imported: list[str] = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
            continue

        if isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    assert [
        name for name in imported
        if name.startswith("orbits.database.models")
    ] == []
