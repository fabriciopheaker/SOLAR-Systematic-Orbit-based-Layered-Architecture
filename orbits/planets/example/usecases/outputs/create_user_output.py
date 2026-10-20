"""
O contrato de SAÍDA da criação de usuário.

Este é o output do UseCase — a fronteira da responsabilidade de
aplicação. Ele recebe o contrato produzido pela Persistence (via
Repository) e expõe apenas os dados que a resposta precisa. A senha
não está aqui, nem em forma de hash.

O contrato mora ao lado de quem o PRODUZ: o UseCase.
"""


class CreateUserOutput:
    """
    O contrato de SAÍDA da responsabilidade.

    Recebe o objeto devolvido pelo Repository, que já é o contrato da
    Persistence (`CreateUserOutput` da camada de dados), e o expõe com
    os mesmos campos públicos. Nenhuma conversão de coluna acontece
    aqui: ela já foi feita pela Persistence.
    """

    def __init__(self, data):
        self.id = data.id
        self.nome = data.nome
        self.email = data.email
        self.created_at = data.created_at

