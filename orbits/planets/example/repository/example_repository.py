
from orbits.database.persistence.users.user_persistency import  UserPersistency, user_persistency
from orbits.database.persistence.users.output.create_user_output import CreateUserOutput
from orbits.planets.example.entity.user_entity import UserEntity


class ExampleRepository:

    def __init__(self, users: UserPersistency):
        self.users = users

    def email_taken(self, email: str) -> bool:
        return self.users.email_exists(email)

    def create(self, entity: UserEntity) -> CreateUserOutput:
        return self.users.create(entity)



example_repository = ExampleRepository(user_persistency)

