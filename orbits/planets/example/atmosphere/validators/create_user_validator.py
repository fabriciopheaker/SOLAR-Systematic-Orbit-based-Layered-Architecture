"""
O validador da criação de usuário.

Confere que os campos CHEGARAM. Se o que veio serve é decisão do
UseCase; aqui se responde só "o corpo tem tudo que a entrada exige?".

O validador roda ANTES de o corpo virar `CreateUserInput` — por isso
os nomes são os do CORPO da requisição, e não os do contrato.
"""

from nucleus.security.json_validator import JsonValidator


class CreateUserValidator(JsonValidator):
    """
    Os campos obrigatórios da criação de usuário.
    """

    REQUIRED_FIELDS = ("nome", "email", "senha")

    def __init__(self):
        # `__init__` só CONFIGURA. Quem valida é `validate(payload)`,
        # que o pipeline da Atmosphere chama com o corpo da
        # requisição — por isso não se valida nada aqui.
        super().__init__(required=self.REQUIRED_FIELDS)

