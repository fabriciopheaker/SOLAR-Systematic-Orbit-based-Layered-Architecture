from abc import ABC


class Event(ABC):
    """
    Representa um acontecimento dentro da aplicação SOLAR.

    Eventos específicos podem herdar desta classe para representar
    acontecimentos concretos da aplicação.

    Exemplo:
        UserCreated
        UserUpdated
        UserDeleted
    """

    def __init__(
        self,
        name: str,
        data: dict | None = None
    ) -> None:

        # `name` é a chave que liga quem publica a quem ouve: os
        # dois combinam o nome, e nenhum precisa conhecer o outro.
        self.name = name

        # `or {}` em vez de `data`: quem publica não é obrigado a
        # mandar payload, e o listener nunca recebe None.
        self.data = data or {}