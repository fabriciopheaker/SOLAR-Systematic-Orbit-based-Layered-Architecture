from abc import ABC, abstractmethod
from typing import Callable


class BroadcastDriver(ABC):
    """
    Contrato de publicação de eventos da SOLAR.

    O driver é só o MECANISMO: ele não sabe o que o evento
    significa nem quem escuta. É essa separação que permite trocar
    o envio em memória por um broker de verdade sem tocar em quem
    publica.
    """

    # `payload` é dict: o evento é DADO, não objeto. O driver não
    # interpreta o conteúdo — quem conhece o formato é quem publica
    # e quem escuta.
    @abstractmethod
    def publish(self, payload: dict) -> None:
        """
        Publica um payload para os consumidores.

        O driver é responsável apenas pelo mecanismo de publicação.
        Ele não deve conhecer a estrutura ou o significado do evento.
        """
        raise NotImplementedError

    @abstractmethod
    def subscribe(
        self,
        event_name: str,
        listener: Callable
    ) -> None:
        """
        Registra um listener para um determinado evento.
        """
        raise NotImplementedError

    # `unsubscribe` existe pelo mesmo motivo que `subscribe`: um
    # listener registrado para sempre é vazamento em processo de
    # vida longa, e um teste que registra precisa poder desfazer.
    @abstractmethod
    def unsubscribe(
        self,
        event_name: str,
        listener: Callable
    ) -> None:
        """
        Remove um listener de um determinado evento.
        """
        raise NotImplementedError