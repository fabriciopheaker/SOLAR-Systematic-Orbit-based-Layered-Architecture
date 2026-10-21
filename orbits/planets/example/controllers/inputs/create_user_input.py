"""
O contrato de ENTRADA da criação de usuário.

A entrada é o que veio do mundo externo, JÁ TRATADO pela Atmosphere. O
construtor RECEBE esse corpo e extrai os campos — quem lê o Controller
vê, na mesma classe, o que a entrada tem.

O contrato mora ao lado de quem o MONTA: o Controller.
"""


class CreateUserInput:
    """
    O contrato de ENTRADA da responsabilidade.

    Os campos são lidos UM A UM (SOLAR-SEG-009): o corpo inteiro nunca
    vira contrato, para que um campo novo na requisição não passe a
    valer sem ninguém decidir.
    """

    def __init__(self, data: dict):
        self.nome = data["nome"]
        self.email = data["email"]
        self.senha = data["senha"]