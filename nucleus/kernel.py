"""
  Montagem da aplicação.

      Kernel().mount()

  Este módulo monta tudo o que a aplicação precisa para atender uma
  requisição: ambiente, identidade, banco, arquivos, eventos,
  middlewares, rotas e tratamento de erro.

  O Kernel MONTA; quem SOBE é o Server (`server.py`).
"""

from pathlib import Path

from flask import Flask, jsonify, request

from nucleus.broadcast.broadcast import Broadcast
from nucleus.broadcast.drivers.in_memory_broadcast import InMemoryBroadcast
from nucleus.database.database import Database
from nucleus.database.drivers.driver_sqlalchemy import DriverSQLAlchemy
from nucleus.environment import Environment
from nucleus.exceptions.contract_exception import ContractException
from nucleus.exceptions.security_exception import SecurityException
from nucleus.exceptions.validation_exception import ValidationException
from nucleus.middleware.error_handler import ErrorHandler
from nucleus.middleware.request_pipeline import RequestPipeline
from nucleus.middleware.security_headers import SecurityHeaders
from nucleus.middleware.security_policy import SecurityPolicy
from nucleus.security.identity import Identity
from nucleus.storage.drivers.local_storage_driver import LocalStorageDriver
from nucleus.storage.storage import Storage
from orbits.routes import routes as orbit_routes


# Raiz do projeto: nucleus/kernel.py → nucleus/ → a raiz da SOLAR.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# O arquivo de ambiente fica DENTRO de nucleus/, junto de quem o
# lê, e não na raiz — na raiz seria mais um arquivo solto.
DEFAULT_ENV_FILE = Path(__file__).resolve().parent / ".env"

# Onde os arquivos enviados pela aplicação são gravados. Fica na
# raiz porque o armazenamento é da aplicação servida, não do
# código: apagar `nucleus/` não pode levar os arquivos dos usuários
# junto.
DEFAULT_STORAGE_ROOT = PROJECT_ROOT / "storage"


class Kernel:
    """
      Monta a aplicação inteira: configuração, mecanismos, rotas e
      observação.

      A ordem da montagem é a ordem das dependências:

          Environment   de onde vêm os valores
          Identity      quem a aplicação é (SECRET_KEY, SOLAR_ID)
          Drivers       a tecnologia (banco, arquivos, eventos)
          Middleware    as proteções de entrada e de saída
          Rotas         o ponto central orbits/routes.py, que agrega
                        as dos Planets

      `mount()` devolve a aplicação pronta. Subir o servidor NÃO é
      papel do Kernel: quem sobe é o Server, que recebe a aplicação.

      O Kernel também NÃO conhece o Observatório — conhece o gancho
      `observe()`. A direção da dependência é Observatory → Nucleus,
      então quem liga os dois é o ponto de montagem, fora dos dois.
    """

    def __init__(
        self,
        env_file=None,
        config=None,
        storage_root=None
    ):
        """
        env_file:
            Arquivo de ambiente (SECRET_KEY, SOLAR_ID). Por padrão,
            `nucleus/.env`.

        config:
            Configuração já lida, para quando ela vem de fora (nos
            testes, por exemplo). Sem ela, quem lê é o Environment.

        storage_root:
            Raiz dos arquivos da aplicação. Por padrão, `storage/`
            na raiz do projeto.
        """

        self.env_file = (
            Path(env_file) if env_file else DEFAULT_ENV_FILE
        )

        self.storage_root = (
            Path(storage_root) if storage_root else DEFAULT_STORAGE_ROOT
        )

        # A configuração pode vir de fora. Os testes passam uma de
        # TEST, com sqlite em memória — assim a montagem é
        # exercitada sem depender do .env nem de banco de verdade.
        self._config = config

        # O que `mount()` preenche. Ficam declarados aqui para que
        # exista UM lugar que diga o que a montagem produz.
        self.config = None
        self.identity = None

        # Mecanismos que ficam à disposição de quem está dentro de
        # uma rota, sem que a rota precise recriá-los.
        self.security = None
        self.request_pipeline = None
        self.response_pipeline = None
        self.error_handler = None

        # A aplicação montada, quando houver uma.
        self.app = None

    # -----------------------------------------------------------------
    # Montagem
    # -----------------------------------------------------------------

    def mount(self) -> Flask:
        """
        Monta a aplicação e devolve pronta para subir.

        O corpo desta função É a receita da montagem, na ordem. Ler
        este bloco de cima para baixo é ler o que acontece quando a
        aplicação sobe.

        Subir o servidor NÃO é papel daqui — quem sobe é o Server.
        """

        # AMBIENTE — de onde vêm os valores
        #
        # O Environment lê o arquivo .env filtrando pelo ambiente
        # ativo: com APP_ENV=DEV ele lê DEV_DB_HOST, DEV_PORT, e
        # assim por diante. O que volta são valores CRUS — quem
        # interpreta cada um é o driver, não aqui.
        self.config = self._config or Environment.init()

        # IDENTIDADE — quem a aplicação é
        #
        # Garante SECRET_KEY (segredo que assina sessão e token) e
        # SOLAR_ID (identificador NÃO secreto, usado em log e
        # auditoria). Se ainda não existirem no arquivo de ambiente,
        # são gerados e GRAVADOS nele — é o efeito colateral que faz
        # a montagem não poder rodar duas vezes ao mesmo tempo.
        self.identity = Identity(env_file=str(self.env_file))
        self.identity.init()

        # BANCO DE DADOS
        #
        # A aplicação fala com a fachada `Database` e NUNCA com o
        # driver (SOLAR-ARCH-008). O que o driver monta — dialect,
        # URL de conexão, engine — é decisão dele, a partir do
        # config cru que veio do ambiente.
        #
        # `init` CONECTA e MONTA AS ESTRUTURAS (§8.1): o banco cuida
        # do próprio esquema. Este arquivo não sabe de Model, de
        # tabela nem de sincronização — e quem quiser desligar a
        # montagem desliga no `Database` (`SYNC_ON_START`).
        Database.init(DriverSQLAlchemy(self.config))


        # ARMAZENAMENTO DE ARQUIVOS
        #
        # Mesma ideia das outras fachadas: a aplicação chama
        # `Storage.save/read` e não sabe onde o arquivo foi parar.
        # Aqui, gravação no disco da própria aplicação.
        Storage.init(LocalStorageDriver(self.storage_root))

        # EVENTOS
        #
        # Fachada de publish/subscribe. O driver em memória atende
        # UM processo: trocar por um broker é trocar esta linha, sem
        # tocar em quem publica.
        Broadcast.init(InMemoryBroadcast())

        # MIDDLEWARE — as proteções de entrada, saída e erro
        #
        # Ficam aqui, e não espalhadas por rota: proteção que
        # depende de alguém lembrar de declarar é proteção que uma
        # hora falha. As rotas USAM estes mecanismos; não os criam.
        self.security = SecurityPolicy()
        self.request_pipeline = RequestPipeline()
        self.error_handler = ErrorHandler()

        # APLICAÇÃO
        app = Flask("solar")

        # A mesma chave da identidade assina a sessão do Flask. É o
        # que impede cookie de sessão forjado.
        app.secret_key = self.identity.secret_key

        # CABEÇALHOS DE SEGURANÇA — em toda resposta
        #
        # Os obrigatórios (nosniff, DENY, no-referrer) vão em
        # QUALQUER resposta, inclusive nas de erro: um 500 com
        # conteúdo e sem nosniff também é brecha.
        headers = SecurityHeaders(self.security)

        @app.after_request
        def apply_security_headers(response):

            for name, value in headers.headers().items():

                # Sobrepõe o que a rota tiver definido: ninguém
                # desliga a proteção respondendo diferente.
                response.headers[name] = value

            return response

        # ERROS — mensagem genérica para quem chamou, e o detalhe
        # inteiro para os observadores
        #
        # Registrado em Exception, e não só nas exceções da SOLAR:
        # falha inesperada também vira resposta segura, em vez de
        # página de erro do servidor.
        @app.errorhandler(Exception)
        def handle_error(error):

            # A tradução de exceção em código HTTP fica aqui, e não
            # na exceção: a exceção fala da regra quebrada, o código
            # fala com o cliente.
            #
            #   400  erro de quem chamou (entrada inválida, contrato)
            #   403  segurança (token, URL, permissão)
            #   500  o resto — e o resto NUNCA diz o que foi
            status = 500

            if isinstance(error, (ValidationException, ContractException)):
                status = 400

            elif isinstance(error, SecurityException):
                status = 403

            # O payload que sai NÃO leva o detalhe interno: leva
            # código estável, mensagem genérica e a referência que
            # liga esta resposta ao registro (SOLAR-ARCH-028).
            #
            # O contexto vai junto para o registro: método, rota e
            # status são o que permite investigar depois.
            payload = self.error_handler.handle(
                error,
                {
                    "method": request.method,
                    "route": request.path,
                    "status": status,
                },
            )

            return jsonify(payload), status

        # ROTAS — o ponto central agrega as dos Planets
        #
        # O Kernel não conhece Planet nenhum: ele registra o que o
        # ponto central montou. Planet novo não muda este arquivo.
        app.register_blueprint(orbit_routes())

        # MECANISMOS — deixados à mão de quem está dentro de uma
        # rota, para não recriar o que já está montado.
        app.extensions["solar"] = self

        self.app = app

        return app

    def observe(self, *observers) -> None:
        """
        Liga observadores ao tratamento de erro.

        Cada observador é um callable (erro, payload, contexto) —
        o gancho por onde o Observatório recebe os erros sem que o
        Nucleus precise conhecê-lo.
        """

        self.error_handler.observe(*observers)

    def shutdown(self) -> None:
        """
        Encerra o que segura recurso.
        """

        # As fachadas de arquivo e evento não seguram conexão; o
        # banco segura, e é ele que precisa ser fechado.
        Database.close()
