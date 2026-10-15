from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class SecurityPolicy:
    """
    Configuração das proteções HTTP da SOLAR.

    A política separa o que é OBRIGATÓRIO do que é OPCIONAL:

        OBRIGATÓRIO — sempre aplicado, sem configuração:
            X-Content-Type-Options, X-Frame-Options,
            Referrer-Policy
            (ver SecurityHeaders.MANDATORY)

        OPCIONAL — ligado por configuração:
            Content-Security-Policy, Strict-Transport-Security,
            Rate limiting, Proteção contra brute force

    Assim a proteção básica NÃO depende de alguém lembrar de
    configurar, e o que é específico de cada aplicação fica
    explícito.
    """

    # Cabeçalhos opcionais.
    content_security_policy: str | None = None
    strict_transport_security: str | None = None
    extra_headers: Mapping[str, str] = field(default_factory=dict)

    # Rate limiting (opcional).
    #
    # 60 requisições por minuto é um ponto de partida conservador
    # para uma API de uso humano: quem precisa de mais, declara.
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    # Proteção contra brute force (opcional).
    #
    # Cinco tentativas e cinco minutos de bloqueio: o bastante para
    # atrapalhar quem tenta adivinhar, e curto o suficiente para
    # não travar quem só esqueceu a senha.
    brute_force_enabled: bool = False
    brute_force_max_attempts: int = 5
    brute_force_lock_seconds: int = 300

    # Proteção CSRF.
    #
    # Diferente das duas acima, esta vem LIGADA por padrão: é
    # defesa em profundidade aplicada pelo pipeline — não uma
    # exigência declarada rota a rota.
    csrf_enabled: bool = True

    # O token acompanha a sessão: uma hora é o mesmo prazo que a
    # sessão típica dura.
    csrf_ttl_seconds: int = 3600
