# Repository do Planet User.
#
# É a fronteira entre o Planet e o banco. Recebe a Persistence do
# Orbit Database por injeção e nunca conhece driver nem ORM — é o
# que a SOLAR-ARCH-002 e a SOLAR-ARCH-003 verificam.
from orbits.database.persistence.persistence import Persistence


class UserRepository:
    """
    Repository responsável pelo acesso aos dados do Planet User.

    O Repository não acessa diretamente:
        - Database;
        - DatabaseDriver;
        - ORM;
        - SQLAlchemy;
        - conexão com o banco.

    Toda persistência deve ser realizada através da
    camada Persistence do Orbit Database.
    """

    def __init__(self, persistence: Persistence):
        """
        Recebe a Persistence através de injeção de dependência.

        A implementação concreta da Persistence é fornecida
        externamente ao Repository.
        """
        # Recebida, e não criada aqui: quem monta decide qual
        # Persistence usar. Instanciar dentro do Repository
        # engessaria o Planet à implementação concreta — que é
        # exatamente o que a injeção existe para evitar.
        self.persistence = persistence