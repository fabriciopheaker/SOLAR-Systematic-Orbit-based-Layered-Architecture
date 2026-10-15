

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
    Responsável pelas operações de persistência da aplicação.

    A Persistence atua como intermediária entre os Repositories
    dos Planets e a infraestrutura de banco disponibilizada
    pelo Nucleus.Database.

    Repositories não devem acessar diretamente:
        - Database;
        - DatabaseDriver;
        - ORM;
        - SQLAlchemy;
        - detalhes de conexão.

    Essas responsabilidades pertencem às camadas inferiores.
    """

    def __init__(self, database):
        """
        Inicializa a Persistence com a infraestrutura
        de banco disponibilizada pelo Nucleus.
        """
        # Recebida do Kernel, não criada aqui: quem monta decide de
        # qual banco se trata, e a Persistence decide como usá-lo.
        self.database = database

        # Cada conjunto de dados tem a sua persistência. Esta camada
        # entrega a PORTA e não conhece as operações de cada uma —
        # quem conhece é quem chama.
        self._users = UserPersistency(database)

    def users(self) -> UserPersistency:
        """
        Persistência dos usuários.
        """

        return self._users