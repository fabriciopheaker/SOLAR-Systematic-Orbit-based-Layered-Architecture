from math import ceil

from nucleus.middleware.security_policy import SecurityPolicy
from nucleus.security.attempt_tracker import AttemptTracker


class RateLimiter:
    """
    Rate limiting: limita a quantidade de requisições por CHAVE
    dentro de uma JANELA de tempo.

    A chave identifica quem é limitado:

        RateLimiter().allow("ip:203.0.113.7")
        RateLimiter().allow("user:42")
        RateLimiter().allow("route:/login")

    É OPCIONAL: desligado na SecurityPolicy
    (`rate_limit_enabled=False`), `allow()` sempre devolve True.

    A responsabilidade do middleware é responder 429 com
    `Retry-After` quando `allow()` devolver False.
    """

    def __init__(
        self,
        policy: SecurityPolicy | None = None,
        tracker: AttemptTracker | None = None
    ):
        self.policy = policy or SecurityPolicy()
        self.tracker = tracker or AttemptTracker()

    def allow(self, key: str) -> bool:
        """
        Registra a requisição e diz se ela pode prosseguir.
        """

        # Desligado na política, `allow` responde True na saída
        # mais barata possível: ele é chamado em TODA requisição.
        if not self.policy.rate_limit_enabled:
            return True

        window = self.policy.rate_limit_window_seconds

        # Confere ANTES de registrar: a requisição que está chegando
        # é justamente a que pode exceder o limite. Registrar e
        # depois conferir deixaria passar a requisição N+1.
        if self.tracker.count(key, window) >= self.policy.rate_limit_requests:
            return False

        self.tracker.record(key)

        return True

    def retry_after(self, key: str) -> int:
        """
        Segundos até a próxima requisição ser aceita.
        """

        window = self.policy.rate_limit_window_seconds

        oldest = self.tracker.oldest(key, window)

        if oldest is None:
            return 0

        # A vaga volta quando a tentativa mais ANTIGA da janela
        # sair dela — é esse o momento em que a contagem cai abaixo
        # do limite outra vez.
        remaining = (oldest + window) - self.tracker.now()

        # Arredonda para cima e nunca devolve negativo: o cabeçalho
        # `Retry-After` não aceita valor fracionário nem negativo.
        return max(0, ceil(remaining))

    def reset(self, key: str) -> None:
        """
        Zera a contagem da chave.
        """

        self.tracker.reset(key)
