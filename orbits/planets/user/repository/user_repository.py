# Repository do Planet User.
#
# É a fronteira entre o Planet e o banco. Recebe a Persistence do
# Model de usuário por injeção e nunca conhece driver nem ORM — é o
# que a SOLAR-RED-002 e a SOLAR-RED-003 verificam.
from orbits.database.persistence.users.user_persistency import (
    UserPersistency,
)


class UserRepository:
    """
    Repository responsável pelo acesso aos dados do Planet User.

    O Repository não acessa diretamente:
        - Database;
        - DatabaseDriver;
        - ORM;
        - SQLAlchemy;
        - conexão com o banco.

    Toda persistência deve ser realizada através da Persistence
    correspondente ao Model — no caso, `UserPersistency`.
    """

    def __init__(self, users: UserPersistency):
        """
        Recebe a Persistence através de injeção de dependência.

        A implementação concreta da Persistence é fornecida
        externamente ao Repository.
        """
        # Recebida, e não criada aqui: quem monta é o Kernel, e o
        # Repository conhece somente a Persistence do Model de que
        # precisa.
        self.users = users
