from typing import Mapping

from nucleus.middleware.security_policy import SecurityPolicy


class SecurityHeaders:
    """
    Cabeçalhos de segurança HTTP.

    MANDATORY — sempre aplicados, sem configuração:

        X-Content-Type-Options: nosniff
        X-Frame-Options: DENY
        Referrer-Policy: no-referrer

    OPCIONAIS — entram pela SecurityPolicy:

        Content-Security-Policy
        Strict-Transport-Security
        + extra_headers

    Os cabeçalhos de segurança SOBREPÕEM o que a aplicação já
    tiver definido: ninguém desliga a proteção respondendo
    diferente.
    """

    # Por que ESTES três não são configuráveis.
    #
    # Os três são baratos e não atrapalham uma API correta:
    #
    #   nosniff       impede o navegador de adivinhar o tipo do
    #                 conteúdo e executar o que era para ser lido;
    #   DENY          impede a página de ser embutida num iframe
    #                 de outro site (clickjacking);
    #   no-referrer   impede a URL de origem de vazar para o
    #                 destino do link.
    MANDATORY: Mapping[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
    }

    CONTENT_SECURITY_POLICY = "Content-Security-Policy"
    STRICT_TRANSPORT_SECURITY = "Strict-Transport-Security"

    def __init__(self, policy: SecurityPolicy | None = None):
        self.policy = policy or SecurityPolicy()

    def headers(self) -> dict[str, str]:
        """
        Cabeçalhos que devem ser aplicados.
        """

        headers = dict(self.MANDATORY)

        if self.policy.content_security_policy:
            headers[self.CONTENT_SECURITY_POLICY] = (
                self.policy.content_security_policy
            )

        if self.policy.strict_transport_security:
            headers[self.STRICT_TRANSPORT_SECURITY] = (
                self.policy.strict_transport_security
            )

        headers.update(self.policy.extra_headers)

        return headers

    def apply(
        self,
        headers: Mapping[str, str] | None = None
    ) -> dict[str, str]:
        """
        Aplica os cabeçalhos de segurança sobre os cabeçalhos da
        resposta.
        """

        # O que a rota definiu entra primeiro, e os de segurança
        # SOBREPÕEM: ninguém desliga a proteção respondendo
        # diferente.
        return {**(headers or {}), **self.headers()}
