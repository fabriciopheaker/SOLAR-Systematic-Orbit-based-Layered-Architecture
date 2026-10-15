import hmac
import secrets
import time
from typing import Callable

from nucleus.exceptions.security_exception import SecurityException


class CsrfProtection:
    """
    Emite e confere o token CSRF.

    Uso:

        csrf = CsrfProtection()
        token = csrf.issue(session_id)      # vai no formulário/
                                            # cabeçalho da resposta
        csrf.validate(session_id, token)    # antes do UseCase

    O token é por SESSÃO e expira (TTL): um token vazado deixa de
    servir sozinho depois do prazo.

    A comparação usa `hmac.compare_digest`, que gasta o mesmo
    tempo para acerto e erro. Comparação comum (`==`) para no
    primeiro caractere diferente e deixa medir o token
    caractere a caractere.

    ESTADO EM MEMÓRIA (processo local). Para várias instâncias da
    aplicação, troque o armazenamento mantendo este contrato.
    """

    HEADER = "X-CSRF-Token"
    FIELD = "csrf_token"

    # solar:allow-secret (código de erro, não credencial)
    INVALID_TOKEN = "INVALID_CSRF_TOKEN"

    def __init__(
        self,
        ttl_seconds: int = 3600,
        clock: Callable[[], float] | None = None,
        token_factory: Callable[[], str] | None = None
    ):
        self.ttl_seconds = ttl_seconds
        self._clock = clock or time.monotonic
        self._factory = token_factory or self._random_token
        self._tokens: dict[str, tuple[str, float]] = {}

    @staticmethod
    def _random_token() -> str:

        # `secrets` e não `random`: o `random` é previsível a partir
        # do estado anterior — quem vê alguns tokens consegue
        # adivinhar o próximo.
        return secrets.token_urlsafe(32)

    def issue(self, session: str) -> str:
        """
        Emite (ou renova) o token da sessão.
        """

        token = self._factory()

        # Renova a cada emissão: o token vazado ontem deixa de valer
        # quando a sessão emite outro hoje.
        self._tokens[session] = (
            token,
            self._clock() + self.ttl_seconds
        )

        return token

    def token(self, session: str) -> str | None:
        """
        Token vigente da sessão, ou None se não existe/expirou.
        """

        entry = self._tokens.get(session)

        if entry is None:
            return None

        token, expires = entry

        if expires <= self._clock():

            self._tokens.pop(session, None)

            return None

        return token

    def is_valid(self, session: str, token: object) -> bool:
        """
        Indica se o token apresentado é o da sessão.
        """

        expected = self.token(session)

        # Sem token vigente não há o que comparar: sessão que nunca
        # emitiu, ou que já expirou.
        if expected is None:
            return False

        # O valor vem de um cabeçalho ou de um formulário, então
        # pode chegar de qualquer tipo — e `compare_digest` exige
        # strings.
        if not isinstance(token, str) or not token:
            return False

        return hmac.compare_digest(expected, token)

    def validate(self, session: str, token: object) -> None:
        """
        Confere o token ou levanta SecurityException.
        """

        if self.is_valid(session, token):
            return

        # As três causas — ausente, expirada, inválida — viram a
        # MESMA resposta de propósito: distinguir as três diria a
        # quem tenta qual parte do token está errada.
        raise SecurityException(
            "Token CSRF ausente, expirado ou inválido.",
            code=self.INVALID_TOKEN
        )

    def reset(self, session: str) -> None:
        """
        Descarta o token da sessão.
        """

        self._tokens.pop(session, None)
