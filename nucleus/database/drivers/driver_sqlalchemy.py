"""
Driver de persistência da SOLAR, sobre SQLAlchemy.

Este é o ÚNICO lugar do projeto que pode importar `sqlalchemy`
(SOLAR-RED-010). Model, Persistence e Planet chegam à ORM pela
fachada `Database`.
"""

from urllib.parse import quote_plus

from .interface.database_driver import DatabaseDriver
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import sqlalchemy

# O Alembic entra aqui porque e ELE quem sabe comparar o banco REAL
# com os Models: o SQLAlchemy sozinho cria o que falta, mas nao
# enxerga o que MUDOU. E biblioteca de banco, e por isso mora no
# driver — o unico lugar do projeto que conhece a tecnologia
# (SOLAR-RED-010).
#
# `produce_migrations` e o mesmo motor do `alembic revision
# --autogenerate`, usado aqui sem arquivo de configuracao e sem
# pasta de migrations: quem aplica o resultado e este driver.
from alembic.autogenerate import produce_migrations
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.operations.ops import (
    DropColumnOp,
    DropConstraintOp,
    DropIndexOp,
    DropTableCommentOp,
    DropTableOp,
    ModifyTableOps,
)

from nucleus.exceptions.database_exception import DatabaseException


class Base(DeclarativeBase):
    """
    Base das entidades da ORM.

    Fica no driver, e não num módulo de Models: quem conhece a
    tecnologia é o driver. Os Models recebem esta base pela fachada
    `Database.model`.
    """

    pass


class DriverSQLAlchemy(DatabaseDriver):
    """
        Driver de persistência da SOLAR baseado em SQLAlchemy.

        É responsabilidade deste driver:

        - interpretar DB_CONNECTION;
        - resolver o dialect/driver do SQLAlchemy;
        - montar a URL de conexão.

        O Environment apenas fornece os valores brutos do ambiente.
    """

    # O que REMOVE alguma coisa do banco.
    #
    # As quatro sao listadas uma a uma porque no Alembic elas NAO
    # tem uma base comum: cada uma herda por conta propria, e um
    # `isinstance` num ancestral unico nao existe. Uma remocao fora
    # desta lista ficaria no banco para sempre, mesmo com `prune`.
    REMOVAL_OPERATIONS = (
        DropTableOp,
        DropColumnOp,
        DropIndexOp,
        DropConstraintOp,
        DropTableCommentOp,
    )

    # Traduz o que está no ambiente para o que a ORM entende.
    #
    # A aplicação escreve `DB_CONNECTION=postgres`; quem sabe que
    # isso vira `postgresql+psycopg` é o driver — é por isso que o
    # Environment devolve o valor CRU, sem interpretar.
    __CONNECTION_CONFIG = {
        "postgres": {
            "dialect": "postgresql",
            "driver": "psycopg",
        },
        "sqlite": {
            "dialect": "sqlite",
            "driver": "pysqlite",
        },
    }

    def __init__(self, config):
        self.config = config
        self.engine = None

        # `_session` e não `session`: o nome sem `_` é o do MÉTODO
        # do contrato, que entrega a sessão. Atributo e método não
        # podem ter o mesmo nome.
        self._session = None

    def connect(self) -> None:

        # O engine guarda o pool de conexões. Criar aqui é o que faz
        # a montagem falhar cedo quando a URL está errada.
        self.engine = sqlalchemy.create_engine(
            self._build_connection_url()
        )

        # A sessão é o que os Repositories usam para consultar.
        #
        # O atributo tem `_` porque o nome sem ele é do MÉTODO do
        # contrato, que é por onde a Persistence a alcança.
        Session = sessionmaker(bind=self.engine)
        self._session = Session()

    def _build_connection_url(self):
        """
            Monta a URL de conexão a partir da configuração do ambiente.

            O dialect/driver é resolvido a partir de DB_CONNECTION e a
            URL é montada internamente com os demais parâmetros
            (DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASS).
        """

        connection = self.config.get("DB_CONNECTION")

        database = self.__CONNECTION_CONFIG.get(connection)

        if database is None:
            raise DatabaseException(
                f"Conexão de banco '{connection}' não suportada.",
                code="INVALID_DATABASE_CONNECTION"
            )

        dialect = database["dialect"]
        driver = database["driver"]

        # SQLite não tem host, porta, usuário nem senha: a URL é o
        # caminho do arquivo — ou `:memory:`, que é o que o
        # ambiente TEST usa para rodar sem banco nenhum.
        if dialect == "sqlite":
            return (
                f"{dialect}"
                f"+{driver}:///"
                f"{self.config['DB_NAME']}"
            )

        # `quote_plus` porque usuário e senha viram parte da URL:
        # uma senha com `@`, `:` ou `/` montaria uma URL quebrada
        # — ou, pior, apontando para outro host.
        user = quote_plus(str(self.config["DB_USER"]))
        password = quote_plus(str(self.config["DB_PASS"]))

        return (
            f"{dialect}"
            f"+{driver}://"
            f"{user}:{password}@"
            f"{self.config['DB_HOST']}:"
            f"{self.config['DB_PORT']}/"
            f"{self.config['DB_NAME']}"
        )

    def disconnect(self):
        # Sessão primeiro, engine depois: a sessão usa o engine.
        if self._session:
            self._session.close()
            self._session = None

        # `dispose` fecha o POOL. Sem ele, as conexões abertas
        # continuam abertas depois de a aplicação parar.
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def health_check(self):
        if self.engine is None:
            raise RuntimeError(
                "O driver SQLAlchemy não está conectado."
            )

        # `SELECT 1` não depende de tabela nenhuma: testa a
        # CONEXÃO, e não o esquema. Se a tabela mudar, o health
        # check continua válido.
        with self.engine.connect() as connection:
            connection.execute(sqlalchemy.text("SELECT 1"))

        return True
    
    def orm(self):
        """
            Retorna a infraestrutura ORM disponibilizada
            pelo driver SQLAlchemy.
        """
        return Base

    def model(self):
        """
            Retorna a infraestrutura ORM disponibilizada
            pelo driver SQLAlchemy.
        """
        return sqlalchemy

    def session(self):
        """
            Retorna a sessão de trabalho da ORM.
        """

        if self._session is None:
            raise DatabaseException(
                "O driver SQLAlchemy não está conectado.",
                code="DATABASE_NOT_CONNECTED"
            )

        return self._session

    def sync(self, *, prune=True):
        """
            Sincroniza o esquema do banco com os Models.

            Duas etapas, nesta ordem:

            1. cria o que ainda NAO existe — a tabela inteira, com
               indices e chaves, como o Model declara;
            2. altera o que JA EXISTE e mudou: coluna nova, tipo
               diferente, obrigatoriedade diferente.

            A ordem nao e gosto: a comparacao da etapa 2 e feita
            DEPOIS da etapa 1, entao o que a etapa 1 criou nao
            aparece mais como diferenca.

            `prune` REMOVE o que existe no banco e nao existe mais
            no Model — coluna, indice ou tabela. E o padrao: um
            esquema que so CRESCE acumula lixo, e a coluna que saiu
            do Model continua aceitando escrita de quem nao sabe que
            ela deixou de existir.
        """

        if self.engine is None:
            raise DatabaseException(
                "O driver SQLAlchemy não está conectado.",
                code="DATABASE_NOT_CONNECTED"
            )

        # So as tabelas dos Models que foram IMPORTADOS: a base da
        # ORM conhece o que ja passou pelo import. Quem importa e a
        # fachada `Database`, antes de chegar aqui.
        Base.metadata.create_all(self.engine)

        self._apply_changes(prune=prune)

    def _apply_changes(self, *, prune=False):
        """
            Aplica no banco o que os Models pedem e ele ainda nao tem.
        """

        # `begin()`: o que a comparacao encontrar e aplicado numa
        # transacao so. Se uma alteracao falhar, nenhuma fica pela
        # metade — e o esquema nao vira um meio-termo que ninguem
        # consegue explicar depois.
        with self.engine.begin() as connection:

            # `compare_type`: sem isso o diff so olharia nomes de
            # coluna, e uma coluna que mudou de tipo passaria batido.
            context = MigrationContext.configure(
                connection,
                opts={"compare_type": True}
            )

            # Quem compara e o Alembic. Reimplementar este diff a mao
            # seria a receita para um dia apagar dado por engano.
            script = produce_migrations(context, Base.metadata)

            operations = [
                operation
                for operation in self._flatten(script.upgrade_ops.ops)
                if prune or not isinstance(operation, self.REMOVAL_OPERATIONS)
            ]

            # Nada mudou: nao ha o que executar, e a subida segue.
            if not operations:
                return

            runner = Operations(context)

            for operation in operations:
                runner.invoke(operation)

    @staticmethod
    def _flatten(operations):
        """
            Abre os grupos por tabela numa lista so.

            O Alembic agrupa as alteracoes de uma mesma tabela em
            `ModifyTableOps`, que e um AGRUPAMENTO e nao uma
            operacao: ele nao pode ser executado, so o que esta
            dentro dele.
        """

        for operation in operations:

            if isinstance(operation, ModifyTableOps):
                yield from DriverSQLAlchemy._flatten(operation.ops)
                continue

            yield operation