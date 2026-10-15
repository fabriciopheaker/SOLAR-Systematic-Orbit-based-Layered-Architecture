from typing import Callable

from nucleus.broadcast.drivers.interface.broadcast_driver import (
    BroadcastDriver
)


class InMemoryBroadcast(BroadcastDriver):
    """
    Driver de eventos em MEMÓRIA.

    Vale para UM processo. Com várias instâncias da aplicação, um
    evento publicado numa não chega a quem ouve na outra — trocar
    por um broker é trocar o driver em `Broadcast.init`.
    """

    def __init__(self) -> None:

        # Nome do evento → listeners registrados para ele.
        self.listeners: dict[str, list[Callable]] = {}

    def publish(self, payload: dict) -> None:

        event_name = payload["name"]

        # Lista vazia quando ninguém ouve: evento sem listener é
        # normal, e não erro.
        listeners = self.listeners.get(event_name, [])

        # Chamada SÍNCRONA, na ordem do registro: quem publica
        # espera os listeners terminarem antes de seguir.
        for listener in listeners:
            listener(payload)

    def subscribe(
        self,
        event_name: str,
        listener: Callable
    ) -> None:

        if event_name not in self.listeners:
            self.listeners[event_name] = []

        # O mesmo listener registrado duas vezes seria chamado duas
        # vezes a cada publicação: registra uma só.
        if listener not in self.listeners[event_name]:
            self.listeners[event_name].append(listener)

    def unsubscribe(
        self,
        event_name: str,
        listener: Callable
    ) -> None:

        if event_name not in self.listeners:
            return

        if listener in self.listeners[event_name]:
            self.listeners[event_name].remove(listener)

        if not self.listeners[event_name]:
            del self.listeners[event_name]