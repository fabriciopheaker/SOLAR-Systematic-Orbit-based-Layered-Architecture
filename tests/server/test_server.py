from types import SimpleNamespace

from nucleus.exceptions.validation_exception import ValidationException
from nucleus.kernel import PROJECT_ROOT, Kernel
from observatory.records.error_log import ErrorLog
from server import Server


BASE_CONFIG = {
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


class FakeApp:
    """
    Aplicação de mentira: anota como foi mandada subir.
    """

    def __init__(self):

        self.options = None

    def run(self, **options):

        self.options = options


class FakeKernel:
    """
    Kernel de mentira: não monta nada de verdade.

    Serve para conferir COMO o Server manda subir, sem depender do
    Flask nem do banco.
    """

    def __init__(self, config=None):

        self.config = config or BASE_CONFIG
        self.identity = SimpleNamespace(solar_id="app-1", secret_key="k")
        self.observers: list = []
        self.closed = False
        self.app = FakeApp()

    def mount(self):

        return self.app

    def observe(self, *observers):

        self.observers.extend(observers)

    def shutdown(self):

        self.closed = True


def _kernel(tmp_path, config=None):
    """
    Kernel de verdade, isolado por teste.
    """

    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=TEST\n", encoding="utf-8")

    return Kernel(
        env_file=env_file,
        config=config or BASE_CONFIG,
        storage_root=tmp_path / "storage",
    )


# a aplicacao sobe com host e porta do ambiente
def test_run_serves_with_the_configured_host_and_port(tmp_path):

    kernel = FakeKernel()

    server = Server(
        kernel=kernel,
        error_log_path=tmp_path / "solar.sqlite",
        verification_root=tmp_path,
    )

    server.run()

    assert kernel.app.options["host"] == "127.0.0.1"
    assert kernel.app.options["port"] == 5099
    assert kernel.app.options["debug"] is False


# em DEV, sobe em modo de desenvolvimento
def test_run_enables_debug_in_development(tmp_path):

    kernel = FakeKernel(dict(BASE_CONFIG, APP_ENV="DEV"))

    server = Server(
        kernel=kernel,
        error_log_path=tmp_path / "solar.sqlite",
        verification_root=tmp_path,
    )

    server.run()

    assert kernel.app.options["debug"] is True


# o recarregador fica desligado: montar tem efeito colateral
def test_run_keeps_the_reloader_off(tmp_path):

    kernel = FakeKernel()

    server = Server(
        kernel=kernel,
        error_log_path=tmp_path / "solar.sqlite",
        verification_root=tmp_path,
    )

    server.run()

    assert kernel.app.options["use_reloader"] is False


# o Observatorio e ligado pelo Server
def test_run_plugs_the_observatory(tmp_path):

    kernel = FakeKernel()

    server = Server(
        kernel=kernel,
        error_log_path=tmp_path / "solar.sqlite",
        verification_root=tmp_path,
    )

    server.run()

    assert len(kernel.observers) == 1
    assert isinstance(kernel.observers[0], ErrorLog)


# depois de subir, encerra o que segura recurso
def test_run_shuts_down_afterwards(tmp_path):

    kernel = FakeKernel()

    server = Server(
        kernel=kernel,
        error_log_path=tmp_path / "solar.sqlite",
        verification_root=tmp_path,
    )

    server.run()

    assert kernel.closed is True
    assert server.error_log is None


# prepare entrega a aplicacao pronta, de verdade
def test_prepare_returns_the_application(tmp_path):

    server = Server(
        kernel=_kernel(tmp_path),
        error_log_path=tmp_path / "solar.sqlite",
    )

    try:
        app = server.prepare()

        assert app.test_client().get("/solar/health").status_code == 200

    finally:
        server.shutdown()


# cada erro tratado vira um registro no Observatorio
def test_prepare_plugs_the_observatory(tmp_path):

    server = Server(
        kernel=_kernel(tmp_path),
        error_log_path=tmp_path / "solar.sqlite",
    )

    try:
        app = server.prepare()

        @app.route("/boom")
        def boom():
            raise ValidationException("x", code="INVALID_X")

        app.test_client().get("/boom")

        assert server.error_log.count() == 1

    finally:
        server.shutdown()


# ---------------------------------------------------------------------
# Verificacao da arquitetura na subida
# ---------------------------------------------------------------------

def _records(root) -> list:
    """
    Registros de auditoria deixados pela verificacao.
    """

    return sorted((root / "observatory" / "solar" / "check").glob("*.md"))


def _server(tmp_path, kernel=None) -> Server:
    """
    Server com raiz de verificacao isolada. A pasta vazia e um
    projeto sem violacao nenhuma — o resultado e sempre limpo.
    """

    return Server(
        kernel=kernel or FakeKernel(),
        error_log_path=tmp_path / "solar.sqlite",
        verification_root=tmp_path,
    )


# sem raiz injetada, a verificacao varre a raiz do PROJETO — a mesma
# que o Kernel usa, e nao uma segunda definicao dela
#
# a assercao e sobre o CAMINHO, e nao sobre o resultado da varredura:
# varrer o projeto de verdade custa caro (o volume compartilhado do
# Windows e lento) e ja e o que o comando `check` faz na esteira
def test_verification_defaults_to_the_project_root(tmp_path):

    server = Server(
        kernel=FakeKernel(),
        error_log_path=tmp_path / "solar.sqlite",
    )

    assert server.verification_root == PROJECT_ROOT


def test_verification_uses_the_injected_root(tmp_path, capsys):

    server = _server(tmp_path)

    report = server.verify_architecture()

    assert report.is_clean()
    assert "arquitetura: correct" in capsys.readouterr().out


# sem violacao NAO se cria arquivo: a verificacao roda sozinha a cada
# subida, e gravar sempre encheria o diretorio de auditoria
def test_verification_does_not_record_when_clean(tmp_path, capsys):

    server = _server(tmp_path)

    server.verify_architecture()

    capsys.readouterr()

    assert _records(tmp_path) == []


# com violacao, mostra o relatorio E registra
#
# a violacao e a mais simples de provocar: um segredo hardcoded
# (SOLAR-ARCH-020), que nao depende de estrutura de diretorio
# nenhuma
def test_verification_records_when_there_is_a_violation(tmp_path, capsys):

    (tmp_path / "config_secret.py").write_text(
        'SECRET_KEY = "abc123"\n',
        encoding="utf-8"
    )

    server = _server(tmp_path)

    report = server.verify_architecture()

    assert not report.is_clean()
    assert report.status() == "violation"

    output = capsys.readouterr().out

    assert "arquitetura: violation" in output
    assert "SOLAR-ARCH-020" in output
    assert "auditoria:" in output

    records = _records(tmp_path)

    assert len(records) == 1
    assert records[0].name.endswith("-violation.md")


# subir de verdade passa pela verificacao
#
# a verificacao vem ANTES da montagem: o resultado aparece antes do
# banner do servidor
def test_run_verifies_before_mounting(tmp_path, capsys):

    kernel = FakeKernel()

    server = _server(tmp_path, kernel=kernel)

    server.run()

    output = capsys.readouterr().out

    assert "arquitetura: correct" in output
    assert kernel.app.options is not None
