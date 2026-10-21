"""
Fachada de eventos da aplicação.

Publicar e ouvir sem que quem publica saiba quem ouve. O driver
decide COMO (memória hoje, broker depois); a aplicação conhece só
`Broadcast.publish` e `Broadcast.subscribe`.
"""

from typing import Callable

from nucleus.broadcast.drivers.interface.broadcast_driver import (
    BroadcastDriver
)
from nucleus.broadcast.event import Event
from nucleus.exceptions.broadcast_exception import BroadcastException
from nucleus.exceptions.contract_exception import ContractException


class Broadcast:
    """
    Fachada de eventos da aplicação.

    Tudo é `classmethod` e o driver vive em ATRIBUTO DE CLASSE: quem
    publica chama `Broadcast.publish(evento)` sem ter (nem receber) uma
    instância. É a mesma escolha de `Storage` e `Database` — o mecanismo
    é global do processo, e passá-lo de mão em mão seria ruído em toda
    assinatura.
    """

    # `None` até `init` rodar. O estado vive aqui, e não em instância,
    # porque a fachada é usada como classe.
    _driver: BroadcastDriver | None = None

    @classmethod
    def init(cls, driver: BroadcastDriver) -> None:
        """
        Inicializa o mecanismo de Broadcast da aplicação.
        """

        # `isinstance` e não `is None`: um objeto qualquer no lugar do
        # driver passaria pela checagem de ausência e quebraria no
        # primeiro `publish`, longe daqui — onde o diagnóstico é ruim.
        if not isinstance(driver, BroadcastDriver):
            raise ContractException(
                "O driver fornecido não implementa o contrato BroadcastDriver.",
                code="INVALID_BROADCAST_DRIVER"
            )

        # Chamar `init` duas vezes TROCA o driver. É o que permite o
        # teste isolar um cenário do outro.
        cls._driver = driver

    @classmethod
    def publish(cls, event: Event) -> None:
        """
        Publica um evento através do driver configurado.
        """

        # Antes de qualquer coisa: publicar sem driver estouraria em
        # `None.publish`, e a mensagem certa aqui é a de contrato.
        cls._ensure_initialized()

        if not isinstance(event, Event):
            raise ContractException(
                "O objeto fornecido não implementa o contrato Event.",
                code="INVALID_EVENT"
            )

        # O driver recebe um DICT, e não o objeto do evento: os
        # drivers são intercambiáveis, e um objeto Python não
        # viajaria para um broker na rede.
        payload = {
            "name": event.name,
            "data": event.data
        }

        try:
            cls._driver.publish(payload)

        # Exceção da SOLAR passa direto: quem capturar precisa
        # continuar vendo o código estável que veio lá de baixo.
        except BroadcastException:
            raise

        # Qualquer outra vira BroadcastException com código próprio,
        # e a original vai junto em `from error`: o rastro continua
        # no log, sem vazar na mensagem (SOLAR-SEG-008).
        except Exception as error:
            raise BroadcastException(
                "Falha ao publicar evento.",
                code="BROADCAST_PUBLISH_ERROR"
            ) from error

    @classmethod
    def subscribe(
        cls,
        event_name: str,
        listener: Callable
    ) -> None:
        """
        Registra um listener para determinado evento.
        """

        cls._ensure_initialized()

        # `strip()` junto: nome só de espaços não identifica evento
        # nenhum, e deixá-lo passar criaria um canal fantasma.
        if not isinstance(event_name, str) or not event_name.strip():
            raise ContractException(
                "O nome do evento deve ser uma string não vazia.",
                code="INVALID_EVENT_NAME"
            )

        # `callable` e não checagem de tipo: qualquer função, método ou
        # objeto com `__call__` serve, e o que se testa aqui é
        # exatamente a capacidade de ser chamado.
        if not callable(listener):
            raise ContractException(
                "O listener fornecido não é chamável.",
                code="INVALID_LISTENER"
            )

        # Mesmo tratamento do `publish`: exceção da SOLAR passa direto;
        # qualquer outra vira `BroadcastException` com `from error`.
        try:
            cls._driver.subscribe(
                event_name,
                listener
            )

        except BroadcastException:
            raise

        except Exception as error:
            raise BroadcastException(
                "Falha ao registrar listener.",
                code="BROADCAST_SUBSCRIBE_ERROR"
            ) from error

    @classmethod
    def unsubscribe(
        cls,
        event_name: str,
        listener: Callable
    ) -> None:
        """
        Remove um listener de determinado evento.
        """

        # As MESMAS validações de `subscribe`: o par precisa ser
        # exatamente o que foi registrado, senão a remoção não acha o
        # listener — e a assinatura continua viva.
        cls._ensure_initialized()

        if not isinstance(event_name, str) or not event_name.strip():
            raise ContractException(
                "O nome do evento deve ser uma string não vazia.",
                code="INVALID_EVENT_NAME"
            )

        if not callable(listener):
            raise ContractException(
                "O listener fornecido não é chamável.",
                code="INVALID_LISTENER"
            )

        try:
            cls._driver.unsubscribe(
                event_name,
                listener
            )

        except BroadcastException:
            raise

        except Exception as error:
            raise BroadcastException(
                "Falha ao remover listener.",
                code="BROADCAST_UNSUBSCRIBE_ERROR"
            ) from error

    @classmethod
    def _ensure_initialized(cls) -> None:
        """
        Garante que o Broadcast foi inicializado.
        """

        # Checagem isolada em um método porque as TRÊS operações
        # públicas precisam dela, e a mensagem tem de ser a mesma nas
        # três.
        if cls._driver is None:
            raise ContractException(
                "O Broadcast não foi inicializado.",
                code="BROADCAST_NOT_INITIALIZED"
            )