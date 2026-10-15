# Contrato de Resource: a última etapa antes de a resposta sair.
#
# É a fronteira de SAÍDA, o par do Sanitizer/Validator (fronteira de
# entrada). Sem ela, um campo interno nasceria exposto no JSON por
# descuido — e o cliente passaria a depender dele.
from abc import ABC, abstractmethod


class Resource(ABC):
    """
    Contrato de Resource da SOLAR.

    Um Resource recebe o resultado produzido pelo UseCase e o
    transforma na representação que será devolvida ao exterior.

        return UserResource.to_object(output), 201

    A resposta NÃO deve sair da aplicação sem ser processada por um
    Resource.

    O Resource é CHAMADO, e não instanciado. Ele não guarda estado
    entre a entrada e a saída, e o `classmethod` diz isso na
    assinatura: `UserResource(output).to_object()` obrigaria a criar
    um objeto cuja única razão de existir é carregar um argumento
    até o método seguinte.
    """

    @classmethod
    @abstractmethod
    def to_object(cls, data) -> dict:
        """
        Transforma o resultado do UseCase na representação que será
        devolvida ao exterior.

        O retorno é a estrutura que sai na resposta.
        """
        raise NotImplementedError

    @classmethod
    def collection(cls, data) -> list:
        """
        Representa uma COLEÇÃO de resultados.

        Existe para que a lista não seja montada em cada Controller:
        `[UserResource.to_object(user) for user in users]` é a mesma
        ideia repetida em todo lugar, e a repetição é onde um item
        acaba escapando sem passar pelo Resource.
        """
        return [cls.to_object(item) for item in data]
