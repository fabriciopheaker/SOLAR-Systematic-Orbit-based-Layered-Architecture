"""
O Repository do Planet example.

É a FRONTEIRA do Planet com o banco. Ele fala com o `Persistence` e
não conhece Model, ORM nem sessão — o caminho permitido é

    Repository → Persistence → Database        (SOLAR-ARCH-003)
"""

from orbits.database.persistence.persistence import Persistence

from orbits.planets.example.entity.user_entity import (
    UserEntity
)


class ExampleRepository:
    """
    Acesso aos dados dos usuários, pelo lado do Planet.

    Ele TRADUZ: recebe entidade e devolve dados. Quem está acima
    dele — o UseCase — nunca vê o Model.
    """

    def __init__(self, persistence: Persistence):
        # Recebida, e não criada aqui: quem monta decide qual
        # Persistence usar. Instanciar dentro do Repository engessaria
        # o Planet à implementação concreta.
        self.persistence = persistence

    def email_taken(self, email: str) -> bool:
        """
        Indica se já existe usuário com este e-mail.
        """

        return self.persistence.users().email_exists(email)

    def create(self, entity: UserEntity) -> dict:
        """
        Grava o usuário e devolve os dados do registro criado.

        Devolve DADOS, e não o Model: o formato da tabela é detalhe da
        camada de baixo, e quem está acima do Repository não pode
        depender dele.
        """

        saved = self.persistence.users().create(
            name=entity.nome,
            email=entity.email,
            password_hash=entity.senha_hash
        )

        return {
            "id": saved.id_user,
            "nome": saved.name_user,
            "email": saved.email_user,
            "created_at": saved.data_created_user,
        }
