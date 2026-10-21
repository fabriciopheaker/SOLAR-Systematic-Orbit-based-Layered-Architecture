"""
O Resource da criação de usuário.

É a ÚLTIMA etapa antes de a resposta sair: o que o cliente recebe é o
que `to_object` devolve, e não o que o UseCase produziu. É aqui que se
decide o que é público — e o que não é.
"""

from nucleus.contracts.resource import Resource


class UserResource(Resource):
    """
    Representação do usuário criado, na resposta.

    O hash da senha não aparece, e não é por esquecimento: o Resource
    é quem decide o que sai, e credencial não sai (SOLAR-SEG-002).
    Um campo a mais aqui vira contrato público no dia seguinte.
    """

    @classmethod
    def to_object(cls, data) -> dict:
        """
        Monta o corpo da resposta a partir da saída do UseCase.
        """

        return {
            "id": data.id,
            "nome": data.nome,
            "email": data.email,
            "created_at": data.created_at.isoformat(),
        }
