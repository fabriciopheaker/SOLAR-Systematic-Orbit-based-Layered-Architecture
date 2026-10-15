"""
O caso de uso: criar usuário.

É onde mora a DECISÃO do fluxo — o que é um e-mail aceitável, o que
fazer quando o e-mail já existe, quando hashear a senha. O Controller
não decide nada disso; ele orquestra.

    CreateUserInput    o contrato de ENTRADA (o Controller monta)
    CreateUserOutput   o contrato de SAÍDA   (o UseCase produz)
    CreateUserUseCase  a responsabilidade
"""

from nucleus.contracts.responsibility_contract import (
    ResponsibilityContract
)
from nucleus.contracts.use_case import UseCase
from nucleus.database.database import Database

from orbits.database.persistence.persistence import Persistence
from orbits.planets.example.entity.user_entity import UserEntity
from orbits.planets.example.repository.example_repository import (
    ExampleRepository
)
from orbits.planets.example.usecases.outputs.create_user_output import (
    CreateUserOutput
)


class CreateUserUseCase(UseCase):
    """
    Cria um usuário e devolve o contrato de saída.
    """

    def __init__(self, repository: ExampleRepository):
        # O Repository, e não o banco: o UseCase não sabe onde o dado
        # é gravado, e não precisa saber.
        self.repository = repository

    @classmethod
    def contract(cls) -> ResponsibilityContract:
        """
        O contrato DECLARADO da responsabilidade (SOLAR-ARCH-015).

        A ENTRADA é declarada pelo NOME. O `CreateUserInput` mora no
        Controller — é ele que converte o corpo em contrato —, e
        importá-lo aqui inverteria a direção: o UseCase passaria a
        conhecer quem o chama. O nome basta para declarar a
        fronteira.

        A SAÍDA é a classe: o `CreateUserOutput` nasce aqui, e o
        UseCase é o dono dele.
        """

        return ResponsibilityContract(
            owner="CreateUserUseCase.execute",
            input_type="CreateUserInput",
            output_type=CreateUserOutput
        )

    def execute(self, data) -> CreateUserOutput:
        """
        Executa a criação.

        O parâmetro é o CONTRATO de entrada, e não o corpo da
        requisição: converter HTTP em contrato é trabalho do
        Controller, e é o que mantém o UseCase fora do framework.
        """

        # NEGÓCIO, e não estrutura: o validador da entrada já conferiu
        # que o campo VEIO; decidir se o que veio serve é aqui.
        UserEntity.ensure_email_is_valid(data.email)

        verify_email_exists = self.repository.email_taken(data.email)

        UserEntity.verify_email(verify_email_exists)

        # A entidade nasce do CONTRATO, e já com o hash: a senha em
        # texto puro não passa do construtor dela.
        entity = UserEntity(data)

        user_saved = self.repository.create(entity)

        return CreateUserOutput(user_saved)


def create_user_use_case() -> CreateUserUseCase:
    """
    Monta o caso de uso com as suas dependências.

    A montagem fica AQUI, no módulo que conhece a responsabilidade: o
    Controller pede o caso de uso pronto e não precisa saber que
    existem Persistence, Repository e banco no caminho.

    É montado a cada chamada de propósito: o que se cria são objetos
    sem estado — guardar o caso de uso num módulo só criaria um lugar
    onde o `Database` poderia ficar preso depois de um `close()`.
    """

    return CreateUserUseCase(
        repository=ExampleRepository(
            Persistence(Database)
        )
    )
