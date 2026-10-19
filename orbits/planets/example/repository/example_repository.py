
from orbits.database.persistence.users.user_persistency import UserPersistency
from orbits.planets.example.entity.user_entity import UserEntity



class ExampleRepository:

    def __init__(self, users: UserPersistency):
        self.users = users

    def email_taken(self, email: str) -> bool:
        return self.users.email_exists(email)

    def create(self, entity: UserEntity) -> dict:
        return self.users.create(
            name=entity.nome,
            email=entity.email,
            password_hash=entity.senha_hash
        )
