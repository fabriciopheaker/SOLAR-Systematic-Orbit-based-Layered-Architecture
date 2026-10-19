

# Persistência do Orbit Database.
#
# É a camada que fica ENTRE o Repository e a fachada `Database`:
# absorve o "como" (sessão, transação) para que o Repository só
# precise dizer "o quê". Existe para o Repository poder ter lógica
# de consulta sem passar a conhecer a infraestrutura.
from orbits.database.persistence.users.user_persistency import (
    UserPersistency
)


class Persistence:
    """
    Porta de entrada da camada de persistência.

    Esta classe NÃO implementa operações de acesso a dados. Ela
    apenas entrega a Persistence de cada Model; quem conhece as
    operações é a implementação do Model (`UserPersistency`), e o
    Repository recebe exatamente a que precisa.

    A fachada é composta pelo Kernel depois de `Database.init()`.
    Repositories e UseCases não a constroem e não conhecem
    `Database`, driver, ORM, SQLAlchemy nem detalhes de conexão.
    """

    def __init__(self, database):
        """
        Inicializa a Persistence com a infraestrutura
        de banco disponibilizada pelo Nucleus.
        """

        # Cada conjunto de dados tem a sua persistência, e cada uma
        # recebe a fachada do banco. Esta classe não guarda o banco
        # para si: não há operação de dados aqui.
        self._users = UserPersistency(database)

    def users(self) -> UserPersistency:
        """
        Persistência dos usuários.
        """

        return self._users