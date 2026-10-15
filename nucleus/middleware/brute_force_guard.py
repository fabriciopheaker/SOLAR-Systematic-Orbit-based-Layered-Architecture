from math import ceil

from nucleus.middleware.security_policy import SecurityPolicy
from nucleus.security.attempt_tracker import AttemptTracker


class BruteForceGuard:
    """
    Proteção contra BRUTE FORCE: conta as TENTATIVAS FALHAS por
    identidade e bloqueia após N falhas, por um período.

    A chave identifica QUEM está tentando:

        guard.register_failure("email:ana@exemplo.com")
        guard.is_locked("email:ana@exemplo.com")

    Um login bem-sucedido ZERA o contador
    (`register_success`), para não punir quem acertou a senha.

    É OPCIONAL: desligado na SecurityPolicy
    (`brute_force_enabled=False`), nada é contado nem bloqueado.

    A responsabilidade do middleware é responder com bloqueio
    temporário (ex.: 429 com `Retry-After`) quando
    `is_locked()` devolver True.
    """

    def __init__(
        self,
        policy: SecurityPolicy | None = None,
        tracker: AttemptTracker | None = None
    ):
        self.policy = policy or SecurityPolicy()
        self.tracker = tracker or AttemptTracker()

    def is_locked(self, key: str) -> bool:
        """
        Indica se a chave está bloqueada.
        """

        # Desligado na política, nada bloqueia — nem o que já estava
        # contado antes de desligar.
        if not self.policy.brute_force_enabled:
            return False

        return self.tracker.locked_until(key) is not None

    def register_failure(self, key: str) -> None:
        """
        Registra uma falha e bloqueia a chave ao atingir o limite.
        """

        if not self.policy.brute_force_enabled:
            return

        self.tracker.record(key)

        # A janela de contagem é a MESMA duração do bloqueio: contar
        # falhas de muito tempo atrás puniria quem errou ontem e
        # acertou hoje.
        window = self.policy.brute_force_lock_seconds

        # O bloqueio é por CHAVE, e não global: travar todo mundo
        # porque um e-mail errou seria negar o serviço a quem não
        # fez nada.
        if self.tracker.count(key, window) >= self.policy.brute_force_max_attempts:
            self.tracker.lock(
                key,
                self.policy.brute_force_lock_seconds
            )

    def register_success(self, key: str) -> None:
        """
        Zera o histórico da chave após um sucesso.
        """

        # Quem acertou a senha não fica a uma tentativa do
        # bloqueio: o contador existe para punir quem ERRA, e o
        # acerto prova que não era o caso.
        self.tracker.reset(key)

    def retry_after(self, key: str) -> int:
        """
        Segundos restantes de bloqueio.
        """

        until = self.tracker.locked_until(key)

        if until is None:
            return 0

        return max(0, ceil(until - self.tracker.now()))

    def remaining_attempts(self, key: str) -> int:
        """
        Quantas tentativas ainda restam antes do bloqueio.
        """

        window = self.policy.brute_force_lock_seconds

        used = self.tracker.count(key, window)

        return max(0, self.policy.brute_force_max_attempts - used)
