
from nucleus.contracts.use_case import UseCase
from orbits.planets.example.entity.user_entity import UserEntity
from orbits.planets.example.repository.example_repository import ExampleRepository
from orbits.planets.example.usecases.outputs.create_user_output import CreateUserOutput


class CreateUserUseCase(UseCase):


    def __init__(self, repository: ExampleRepository):
        self.repository = repository


    def execute(self, data) -> CreateUserOutput:

        UserEntity.ensure_email_is_valid(data.email)
        verify_email_exists = self.repository.email_taken(data.email)
        UserEntity.verify_email(verify_email_exists)
        entity = UserEntity(data)
        user_saved = self.repository.create(entity)
        return CreateUserOutput(user_saved)

