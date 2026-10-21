"""
Fachada de persistência da aplicação.

A aplicação — Orbits, Planets — fala SEMPRE com `Database` e
NUNCA com o driver (SOLAR-RED-008). Trocar SQLAlchemy por outra
tecnologia é trocar o driver injetado em `init()`, sem tocar em
quem consulta.
"""

import importlib
import pkgutil

from .drivers.interface.database_driver import DatabaseDriver
from nucleus.exceptions.contract_exception import ContractException
from nucleus.exceptions.database_exception import DatabaseException

class Database:


  # O driver ligado em `init()`. Enquanto for None, a aplicação
  # ainda não pode consultar nada.
  _driver: DatabaseDriver | None = None

  # Publicados a partir do driver logo depois da conexão. É por
  # eles que um Model usa a ORM SEM importar sqlalchemy — o que
  # mantém a SOLAR-RED-010 de pé: só o driver conhece a
  # tecnologia.
  orm = None
  model = None

  # De ONDE os Models sao importados.
  #
  # E a unica coisa que a fachada sabe sobre o CONTEUDO do projeto —
  # e ela sabe porque e ela quem monta o banco: a ORM so conhece o
  # Model que ja passou pelo import, e quem importa e ela.
  MODELS_PACKAGE = "orbits.database.models"

  # MONTA as estruturas do banco ao iniciar. E o BOTAO.
  #
  # ATENCAO: em PRODUCAO isto deve ficar DESLIGADO. Sincronizar
  # esquema cria, altera e REMOVE estrutura — e um engano aqui custa
  # dado. Em producao o esquema pertence ao DEPLOY, nao a subida.
  #
  # E tambem o ponto de troca para quem quiser migrations: com
  # `SYNC_ON_START = False`, quem cuida do esquema passa a ser a
  # ferramenta de migracao, rodada antes de subir a aplicacao.
  SYNC_ON_START = True

  @classmethod
  def init(cls, driver: DatabaseDriver) -> None:
    """
      Inicializa o mecanismo de persistência da aplicação.
      O driver recebido deve implementar o contrato DatabaseDriver.
    """


    # Recusa driver fora do contrato na MONTAGEM, e não na
    # primeira consulta em produção.
    if not isinstance(driver, DatabaseDriver):
        raise ContractException(
        "O driver fornecido não implementa o contrato DatabaseDriver.",
        code="INVALID_DATABASE_DRIVER"
    )

    cls._driver = driver

    # A fachada não escolhe a tecnologia: ela repassa o que o
    # driver oferece.
    cls.orm = cls._driver.orm()
    cls.model = cls._driver.model()

    # Conecta já na montagem. Subir com o banco inalcançável falha
    # aqui, com a causa à vista, em vez de falhar na requisição de
    # um usuário.
    cls._driver.connect()

    # E MONTA AS ESTRUTURAS: o banco inicia montado, e não só
    # conectado. Banco conectado sem as tabelas certas é falha
    # adiada para a primeira consulta.
    #
    # A ordem importa: os Models só podem ser importados DEPOIS de
    # `orm` e `model` estarem publicados, porque o Model declara
    # `class Users(Database.orm)` no próprio import.
    if cls.SYNC_ON_START:
      cls.sync()

  @classmethod
  def driver(cls) -> DatabaseDriver:
    """
      Retorna o driver atualmente configurado.
    """

    # Erro de MONTAGEM, não de uso: quem chamou esqueceu de
    # inicializar. O código estável permite separar os dois no log.
    if cls._driver is None:
        raise DatabaseException(
            "O Database ainda não foi inicializado.",
            code="DATABASE_NOT_INITIALIZED"
        )

    return cls._driver



  @classmethod
  def session(cls):
    """
      Retorna a sessão de trabalho da ORM.

      É por onde a Persistence lê e grava. Vem do driver: a fachada
      não cria sessão nenhuma, só repassa o que ele oferece — igual
      ao que já faz com o `orm` e o `model`.
    """

    return cls.driver().session()

  @classmethod
  def sync(cls, *, prune=True) -> list[str]:
    """
      Monta o esquema do banco a partir dos Models.

      Cria o que falta, altera o que mudou e — por padrão — REMOVE o
      que não existe mais no Model.

      Quem sabe fazer isso é o driver. Antes de pedir, a fachada
      IMPORTA os Models: a ORM só conhece o que já passou pelo
      import, e um Model que ninguém importou é, para ela, uma
      tabela que não existe.

      Devolve os módulos de Model que foram importados.
    """

    # Erro de MONTAGEM, não de uso. A checagem vem ANTES dos
    # imports: importar um Model sem ORM publicada estoura lá
    # dentro, sem explicar que faltou inicializar o banco.
    cls.driver()

    imported = cls._import_models()

    cls.driver().sync(prune=prune)

    return imported

  @classmethod
  def _import_models(cls) -> list[str]:
    """
      Importa todos os Models do pacote e devolve os nomes.

      Importar é o que REGISTRA a tabela na ORM: não há registro
      separado. Só o primeiro nível do pacote é varrido, o que basta
      porque a regra do projeto é um Model por ARQUIVO.

      A ordem é ALFABÉTICA, e não a do sistema de arquivos: o
      resultado precisa ser o mesmo em qualquer máquina.
    """

    package = importlib.import_module(cls.MODELS_PACKAGE)

    names = sorted(
      name for _, name, _ in pkgutil.iter_modules(package.__path__)
    )

    imported: list[str] = []

    for name in names:

      module = importlib.import_module(f"{cls.MODELS_PACKAGE}.{name}")

      imported.append(module.__name__)

    return imported

  @classmethod
  def close(cls) -> None:
      """
        Encerra a conexão com o mecanismo de persistência.
      """

      # Fechar duas vezes não é erro: o shutdown roda no `finally`
      # da subida, e pode acontecer depois de um fechamento
      # explícito.
      if cls._driver is None:
          return

      cls._driver.disconnect()

      # Volta ao estado "não inicializado": uma montagem nova
      # precisa injetar um driver novo.
      cls._driver = None