import time
from typing import Callable


class AttemptTracker:
    """
    Registra TENTATIVAS por chave, dentro de uma janela de tempo,
    e controla bloqueios temporários.

    É o estado compartilhado por:

        RateLimiter        → limita requisições por janela;
        BruteForceGuard    → bloqueia após N falhas.

    A chave identifica QUEM é contado (IP, usuário, e-mail...).

    ESTADO EM MEMÓRIA (processo local). Para várias instâncias da
    aplicação, troque por um armazenamento compartilhado mantendo
    este contrato — a lógica de janela permanece a mesma.
    """

    def __init__(self, clock: Callable[[], float] | None = None):

        # `monotonic` e não `time.time()`: o relógio monotônico só
        # anda para a frente.
        #
        # Com o relógio do sistema, bastaria adiantar a hora da
        # máquina para um bloqueio vencer na hora — e o bloqueio é
        # contra quem tenta, então não pode depender de algo que
        # quem tenta consegue mexer.
        #
        # O relógio é injetável para os testes não esperarem de
        # verdade.
        self._clock = clock or time.monotonic

        # Chave → momentos das tentativas.
        self._attempts: dict[str, list[float]] = {}

        # Chave → momento em que o bloqueio termina.
        self._locks: dict[str, float] = {}

    def now(self) -> float:
        """
        Momento atual (injetável, para testes determinísticos).
        """

        return self._clock()

    def record(self, key: str) -> None:
        """
        Registra uma tentativa para a chave.
        """

        self._attempts.setdefault(key, []).append(self.now())

    def count(self, key: str, window: float) -> int:
        """
        Quantidade de tentativas dentro da janela.

        Tentativas fora da janela são descartadas.
        """

        attempts = self._attempts.get(key)

        if not attempts:
            return 0

        threshold = self.now() - window

        kept = [moment for moment in attempts if moment > threshold]

        # A poda acontece na LEITURA, e não por um processo de
        # limpeza à parte: sem ela, o dicionário cresceria para
        # sempre numa aplicação que roda meses.
        if kept:
            self._attempts[key] = kept
        else:
            self._attempts.pop(key, None)

        return len(kept)

    def oldest(self, key: str, window: float) -> float | None:
        """
        Momento da tentativa mais antiga DENTRO da janela.
        """

        self.count(key, window)

        attempts = self._attempts.get(key)

        return attempts[0] if attempts else None

    def reset(self, key: str) -> None:
        """
        Zera tentativas e bloqueio da chave.
        """

        self._attempts.pop(key, None)
        self._locks.pop(key, None)

    def lock(self, key: str, seconds: float) -> None:
        """
        Bloqueia a chave por um período.
        """

        self._locks[key] = self.now() + seconds

    def locked_until(self, key: str) -> float | None:
        """
        Momento em que o bloqueio termina, ou None se livre.

        Bloqueio vencido é descartado.
        """

        until = self._locks.get(key)

        if until is None:
            return None

        # Bloqueio vencido é descartado ao ser consultado: não
        # existir na estrutura e estar vencido significam a mesma
        # coisa — a chave está livre.
        if until <= self.now():
            self._locks.pop(key, None)
            return None

        return until
