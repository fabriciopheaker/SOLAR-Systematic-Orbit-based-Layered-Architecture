from nucleus.middleware.brute_force_guard import BruteForceGuard
from nucleus.middleware.rate_limiter import RateLimiter
from nucleus.middleware.security_headers import SecurityHeaders
from nucleus.middleware.security_policy import SecurityPolicy
from nucleus.security.attempt_tracker import AttemptTracker


class FakeClock:
    """
    Relógio controlável — a janela de tempo vira determinística.
    """

    def __init__(self, now: float = 0.0):
        self.value = now

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


# ---------------------------------------------------------------------
# SecurityHeaders
# ---------------------------------------------------------------------

def test_mandatory_headers_are_always_applied():

    headers = SecurityHeaders().headers()

    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"


def test_optional_headers_come_from_the_policy():

    policy = SecurityPolicy(
        content_security_policy="default-src 'self'",
        strict_transport_security="max-age=31536000",
        extra_headers={"Permissions-Policy": "geolocation=()"}
    )

    headers = SecurityHeaders(policy).headers()

    assert headers["Content-Security-Policy"] == "default-src 'self'"
    assert headers["Strict-Transport-Security"] == "max-age=31536000"
    assert headers["Permissions-Policy"] == "geolocation=()"
    assert headers["X-Frame-Options"] == "DENY"


def test_optional_headers_are_absent_by_default():

    headers = SecurityHeaders().headers()

    assert "Content-Security-Policy" not in headers
    assert "Strict-Transport-Security" not in headers


# a aplicacao NAO consegue desligar um cabecalho de seguranca
def test_security_headers_override_application_headers():

    applied = SecurityHeaders().apply(
        {"X-Frame-Options": "ALLOWALL", "Content-Type": "application/json"}
    )

    assert applied["X-Frame-Options"] == "DENY"
    assert applied["Content-Type"] == "application/json"


# ---------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------

def _limiter(clock, **overrides) -> RateLimiter:

    values = {
        "rate_limit_enabled": True,
        "rate_limit_requests": 3,
        "rate_limit_window_seconds": 60,
    }

    values.update(overrides)

    tracker = AttemptTracker(clock=clock)

    return RateLimiter(SecurityPolicy(**values), tracker)


def test_rate_limiter_is_optional():

    limiter = RateLimiter(SecurityPolicy())

    for _ in range(100):
        assert limiter.allow("ip:1.2.3.4") is True


def test_rate_limiter_allows_up_to_the_limit():

    clock = FakeClock()
    limiter = _limiter(clock)

    assert [limiter.allow("ip:1.2.3.4") for _ in range(4)] == [
        True,
        True,
        True,
        False,
    ]


def test_rate_limiter_reports_retry_after():

    clock = FakeClock()
    limiter = _limiter(clock)

    for _ in range(3):
        limiter.allow("ip:1.2.3.4")

    assert limiter.allow("ip:1.2.3.4") is False
    assert limiter.retry_after("ip:1.2.3.4") == 60

    clock.advance(30)

    assert limiter.retry_after("ip:1.2.3.4") == 30


def test_rate_limiter_frees_the_window():

    clock = FakeClock()
    limiter = _limiter(clock)

    for _ in range(3):
        limiter.allow("ip:1.2.3.4")

    assert limiter.allow("ip:1.2.3.4") is False

    clock.advance(61)

    assert limiter.allow("ip:1.2.3.4") is True


# cada chave tem a sua propria contagem
def test_rate_limiter_isolates_keys():

    clock = FakeClock()
    limiter = _limiter(clock)

    for _ in range(3):
        limiter.allow("ip:1.2.3.4")

    assert limiter.allow("ip:1.2.3.4") is False
    assert limiter.allow("ip:5.6.7.8") is True


# ---------------------------------------------------------------------
# BruteForceGuard
# ---------------------------------------------------------------------

def _guard(clock, **overrides) -> BruteForceGuard:

    values = {
        "brute_force_enabled": True,
        "brute_force_max_attempts": 3,
        "brute_force_lock_seconds": 300,
    }

    values.update(overrides)

    tracker = AttemptTracker(clock=clock)

    return BruteForceGuard(SecurityPolicy(**values), tracker)


def test_brute_force_is_optional():

    guard = BruteForceGuard(SecurityPolicy())

    for _ in range(10):
        guard.register_failure("email:ana")

    assert guard.is_locked("email:ana") is False


def test_brute_force_locks_after_max_attempts():

    clock = FakeClock()
    guard = _guard(clock)

    guard.register_failure("email:ana")
    guard.register_failure("email:ana")

    assert guard.is_locked("email:ana") is False
    assert guard.remaining_attempts("email:ana") == 1

    guard.register_failure("email:ana")

    assert guard.is_locked("email:ana") is True
    assert guard.remaining_attempts("email:ana") == 0
    assert guard.retry_after("email:ana") == 300


def test_brute_force_success_resets_the_counter():

    clock = FakeClock()
    guard = _guard(clock)

    guard.register_failure("email:ana")
    guard.register_failure("email:ana")

    guard.register_success("email:ana")

    assert guard.remaining_attempts("email:ana") == 3
    assert guard.is_locked("email:ana") is False


def test_brute_force_lock_expires():

    clock = FakeClock()
    guard = _guard(clock)

    for _ in range(3):
        guard.register_failure("email:ana")

    assert guard.is_locked("email:ana") is True

    clock.advance(301)

    assert guard.is_locked("email:ana") is False
    assert guard.retry_after("email:ana") == 0


# a chave bloqueada e independente das demais
def test_brute_force_isolates_keys():

    clock = FakeClock()
    guard = _guard(clock)

    for _ in range(3):
        guard.register_failure("email:ana")

    assert guard.is_locked("email:ana") is True
    assert guard.is_locked("email:bob@exemplo.com") is False
