"""
O contrato de SAÍDA da criação de usuário.

Recebe, no CONSTRUTOR, o dicionário que o Repository devolveu — e monta
o contrato a partir dele. Traz o que a resposta precisa, e nada além: a
senha não está aqui, nem em forma de hash.

O contrato mora ao lado de quem o PRODUZ: o UseCase.
"""


class CreateUserOutput:
    """
    O contrato de SAÍDA da responsabilidade.

    Os campos são lidos UM A UM, como na entrada: o dicionário do
    Repository é a matéria-prima, e não o contrato.
    """

    def __init__(self, data: dict):
        self.id = data["id"]
        self.nome = data["nome"]
        self.email = data["email"]
        self.created_at = data["created_at"]
