"""
O fluxo completo do Planet `example`, ponta a ponta.

Estes testes sobem a aplicacao de verdade (sqlite em memoria) e fazem
a requisicao de verdade: rota, guardas, Controller, UseCase,
Repository, Persistence, Model e Resource, todos no caminho.
"""

from nucleus.database.database import Database
from nucleus.kernel import Kernel

from orbits.planets.example.atmosphere.sanitizers.create_user_sanitizer import (  # noqa: E501
    CreateUserSanitizer,
)
from orbits.planets.example.atmosphere.validators.create_user_validator import (  # noqa: E501
    CreateUserValidator,
)


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


def _app(tmp_path):
    """
    Aplicacao montada de verdade, em sqlite de memoria.

    Devolve o Kernel junto porque quem montou e quem encerra: o
    `Database` e global, e deixar a conexao aberta contaminaria o
    teste seguinte.
    """

    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=TEST\n", encoding="utf-8")

    kernel = Kernel(
        env_file=env_file,
        config=CONFIG,
        storage_root=tmp_path / "storage",
    )

    return kernel, kernel.mount()


def _payload(**overrides):
    """
    Corpo valido da criacao, com o que o teste quiser trocar.
    """

    data = {
        "nome": "Ana",
        "email": "ana@exemplo.com",
        "senha": "s3nha-boa",
    }

    data.update(overrides)

    return data


# ---------------------------------------------------------------------
# O caminho feliz
# ---------------------------------------------------------------------

# o fluxo inteiro: rota, guardas, Controller, UseCase, Repository,
# Persistence e Resource
def test_creating_a_user_answers_201_with_the_resource(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        response = app.test_client().post("/examples/users", json=_payload())

        assert response.status_code == 201

        body = response.get_json()

        assert body["nome"] == "Ana"
        assert body["email"] == "ana@exemplo.com"
        assert body["id"] > 0
        assert "created_at" in body

    finally:
        kernel.shutdown()


# o Resource decide o que sai da aplicacao, e credencial NAO sai
# (SOLAR-SEG-002)
def test_the_resource_does_not_expose_the_password(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        body = app.test_client().post(
            "/examples/users",
            json=_payload()
        ).get_json()

        assert "senha" not in body
        assert "senha_hash" not in body

    finally:
        kernel.shutdown()


# o sanitizer roda ANTES de o dado virar contrato: espaco em volta nao
# chega ao que foi gravado
def test_the_sanitizer_trims_the_value_before_persisting(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        body = app.test_client().post(
            "/examples/users",
            json=_payload(nome="   Ana   ")
        ).get_json()

        assert body["nome"] == "Ana"

    finally:
        kernel.shutdown()


# a senha e guardada como HASH, nunca em texto puro
def test_the_password_is_stored_hashed(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        app.test_client().post("/examples/users", json=_payload())

        from orbits.database.models.user_model import Users

        saved = Database.session().query(Users).first()

        assert saved.password_user != "s3nha-boa"

        # Todo hash do bcrypt comeca com o marcador da versao.
        assert saved.password_user.startswith("$2")

    finally:
        kernel.shutdown()


# ---------------------------------------------------------------------
# Quando a entrada nao serve
# ---------------------------------------------------------------------

# campo obrigatorio ausente: 400, com codigo estavel e SEM detalhe
# interno na resposta (SOLAR-SEG-008)
def test_a_missing_field_answers_400(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        response = app.test_client().post(
            "/examples/users",
            json=_payload(nome=None)
        )

        assert response.status_code == 400

        body = response.get_json()

        assert body["code"] == "MISSING_FIELDS"

        # A resposta NAO diz qual campo faltou: quem sabe disso e o
        # log. O cliente recebe codigo e a referencia.
        assert "nome" not in body["message"]
        assert body["reference"]

    finally:
        kernel.shutdown()


# corpo que nao e objeto JSON
def test_a_body_that_is_not_an_object_answers_400(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        response = app.test_client().post(
            "/examples/users",
            json=["nao", "e", "objeto"]
        )

        assert response.status_code == 400
        assert response.get_json()["code"] == "INVALID_JSON_BODY"

    finally:
        kernel.shutdown()


# e-mail sem forma de e-mail e regra de NEGOCIO: quem recusa e o
# UseCase, e nao o validador da entrada
def test_an_invalid_email_answers_400(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        response = app.test_client().post(
            "/examples/users",
            json=_payload(email="ana-arroba-exemplo.com")
        )

        assert response.status_code == 400
        assert response.get_json()["code"] == "INVALID_EMAIL"

    finally:
        kernel.shutdown()


# e-mail ja usado: a segunda criacao e recusada depois de consultar o
# banco
def test_a_repeated_email_answers_400(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        client = app.test_client()

        first = client.post("/examples/users", json=_payload())
        second = client.post("/examples/users", json=_payload())

        assert first.status_code == 201
        assert second.status_code == 400
        assert second.get_json()["code"] == "EMAIL_TAKEN"

    finally:
        kernel.shutdown()


# ---------------------------------------------------------------------
# A fronteira do Planet
# ---------------------------------------------------------------------

# a ROTA do Planet declara quem protege cada entrada: o corpo chega
# ao UseCase tratado pelo guarda DO PLANET (SOLAR-ROF-001)
def test_the_planet_declares_its_frontier(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        blueprint = app.blueprints["orbits.example"]

        sanitizer, validator = blueprint._guards["create_example_user"]

        # Os guardas do PLANET, e nao os genericos: e neles que ficam
        # os campos obrigatorios e a limpeza desta entrada.
        assert isinstance(sanitizer, CreateUserSanitizer)
        assert isinstance(validator, CreateUserValidator)

    finally:
        kernel.shutdown()


# a rota declara o ESSENCIAL — URL, Controller e metodo — e aponta
# para o Controller (SOLAR-ROF-005), mesmo com o adaptador no meio
#
def test_the_route_declares_only_the_essentials(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        # O endpoint vem PREFIXADO pelo agregador (`orbits.example...`),
        # entao a busca e pelo sufixo: o prefixo e decisao de quem
        # agrega, e nao deste teste.
        endpoints = [
            endpoint for endpoint in app.view_functions
            if endpoint.endswith("create_example_user")
        ]

        assert len(endpoints) == 1

        # O nome do chamavel sobrevive ao adaptador: e por ele que a
        # rota aponta para o Controller.
        assert (
            app.view_functions[endpoints[0]].__qualname__
            == "CreateUserController.create"
        )

    finally:
        kernel.shutdown()


# a entrada e tratada ANTES do Controller: o que chega no Controller
# ja passou pela Atmosphere
#
def test_the_atmosphere_treats_the_body_before_the_controller(tmp_path):

    kernel, app = _app(tmp_path)

    try:
        # Espaco em volta e e-mail em MAIUSCULA: os dois tem que sair
        # tratados do outro lado, e o Resource devolve o que o UseCase
        # gravou.
        body = app.test_client().post(
            "/examples/users",
            json=_payload(nome="   Ana   ", email="Ana@Exemplo.com")
        ).get_json()

        assert body["nome"] == "Ana"
        assert body["email"] == "ana@exemplo.com"

    finally:
        kernel.shutdown()
