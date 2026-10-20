"""
Contrato de SAÍDA da Persistence de usuário.

Este é o output da CAMADA DE PERSISTÊNCIA: quem o produz é a
`UserPersistency`, e quem o consome é o Repository do Planet. Ele não
é o `CreateUserOutput` do UseCase — são contratos diferentes, com
donos diferentes:

    Model → UserPersistency → CreateUserOutput (Persistence)
          → Repository → CreateUserOutput (UseCase) → Resource

Aqui acontece a tradução dos nomes das COLUNAS (`id_user`,
`name_user`, `email_user`, `data_created_user`) para os nomes
PÚBLICOS do contrato (`id`, `nome`, `email`, `created_at`). O
Repository não repete essa conversão.
"""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class CreateUserOutput:
    """
    Dados do usuário persistido, já sem os nomes do Model.

    `created_at` continua sendo `datetime`: serializar é decisão da
    borda HTTP (o Resource), não da camada de persistência.
    """

    id: int
    nome: str
    email: str
    created_at: datetime

    @classmethod
    def to_object(cls, user) -> "CreateUserOutput":
        """
        Converte o Model persistido no contrato de saída.

        `user` é o PRÓPRIO Model — não um invólucro com `.user`.
        Os atributos lidos são os que existem em `Users`.
        """

        created_at = user.data_created_user

        # Em bancos que devolvem o default só depois do INSERT, o
        # atributo pode chegar vazio; o contrato de dados não pode.
        if not isinstance(created_at, datetime):
            created_at = datetime.now(timezone.utc)

        return cls(
            id=user.id_user,
            nome=user.name_user,
            email=user.email_user,
            created_at=created_at,
        )
