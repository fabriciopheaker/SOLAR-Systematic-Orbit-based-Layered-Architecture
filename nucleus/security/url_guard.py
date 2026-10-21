# Guarda de URL: barra destino não confiável ANTES da chamada externa.
#
# É o instrumento que a SOLAR-SEG-010 aponta quando a URL precisa mesmo
# variar em tempo de execução — a regra proíbe montar URL com dado de
# entrada, e este é o caminho permitido para o caso legítimo.
#
# Estático e SEM REDE: não há resolução de DNS aqui (ver o docstring da
# classe) — resolver seria uma consulta de rede dentro do validador, e o
# validador precisa ser previsível.
from ipaddress import ip_address
from urllib.parse import urlsplit

from nucleus.exceptions.security_exception import SecurityException


class UrlGuard:
    """
    Valida uma URL ANTES de a aplicação buscar um serviço externo
    (SOLAR-SEG-010).

    É o instrumento para os casos que precisam variar em tempo de
    execução — em vez de a URL ir crua para o cliente HTTP:

        UrlGuard(allowed_hosts=["api.exemplo.com"]).validate(url)
        requests.get(url, ...)

    O que é barrado:

        esquema fora da lista              file:///etc/passwd
        endereço INTERNO                   http://169.254.169.254
                                           http://127.0.0.1
                                           http://10.0.0.5
                                           http://[::1]
        host fora da lista permitida       http://outro.com
        credenciais na URL                 http://user:senha@host

    O bloqueio de endereço interno vale para IP LITERAL, que é como
    a maioria dos ataques tenta alcançar o metadata service
    (169.254.169.254). Um NOME que resolve para endereço interno
    só é barrado pela lista de hosts permitidos: resolver DNS aqui
    seria uma consulta de rede dentro do validador.

    Por isso a lista de hosts permitidos é a defesa principal. Sem
    ela, o guard ainda barra esquema, credenciais e IP interno,
    mas não sabe para onde um nome aponta.
    """

    # Só `https` por padrão. `http` fica de fora DE PROPÓSITO: o caso
    # comum é serviço externo, e `http` puro expõe a chamada. Quem
    # precisa de outro esquema passa `allowed_schemes`.
    DEFAULT_SCHEMES = ("https",)

    # Um código por MOTIVO da recusa: quem trata a exceção distingue
    # "host não permitido" de "esquema errado" sem ler a mensagem.
    INVALID_URL = "INVALID_URL"
    DISALLOWED_SCHEME = "DISALLOWED_SCHEME"
    DISALLOWED_HOST = "DISALLOWED_HOST"
    PRIVATE_ADDRESS = "PRIVATE_ADDRESS"

    # Código de erro, não credencial — o marcador diz isso à
    # SOLAR-SEG-001, que acusaria o nome pelo vocabulário.
    # solar:allow-secret (código de erro, não credencial)
    URL_CREDENTIALS = "URL_CREDENTIALS"

    def __init__(
        self,
        allowed_hosts=None,
        allowed_schemes=None
    ):
        # `None` significa "não há lista" — e é DIFERENTE de lista vazia,
        # que barraria todo host. `_validate_host` usa essa diferença
        # para saber se a checagem se aplica.
        #
        # `strip().lower()` na entrada: a lista é escrita à mão na
        # configuração, e `"API.exemplo.com "` tem que valer o mesmo
        # que `"api.exemplo.com"`.
        self.allowed_hosts = (
            frozenset(
                host.strip().lower()
                for host in allowed_hosts
            )
            if allowed_hosts is not None
            else None
        )

        self.allowed_schemes = frozenset(
            scheme.strip().lower()
            for scheme in (allowed_schemes or self.DEFAULT_SCHEMES)
        )

    def is_allowed(self, url) -> bool:
        """
        Indica se a URL pode ser usada.
        """

        # Pergunta de SIM ou NÃO para quem só quer decidir sem tratar
        # exceção — `validate` continua sendo o caminho quando se quer o
        # MOTIVO.
        try:
            self.validate(url)
        except SecurityException:
            return False

        return True

    def validate(self, url) -> None:
        """
        Valida a URL ou levanta SecurityException.
        """

        # Tipo antes de conteúdo: `urlsplit` de algo que não é texto
        # estouraria com erro de tipo, e não de segurança.
        if not isinstance(url, str) or not url.strip():

            raise SecurityException(
                "URL vazia ou de tipo inválido.",
                code=self.INVALID_URL
            )

        # `urlsplit` UMA vez, e as partes passadas adiante: cada
        # checagem olha um pedaço diferente da mesma análise.
        parts = urlsplit(url)

        self._validate_scheme(parts)
        self._validate_credentials(parts)

        # O host é extraído no meio porque as duas checagens seguintes
        # precisam dele — e é ele que levanta se estiver ausente.
        host = self._host(parts)

        # Duas defesas em ordem: primeiro o endereço LITERAL (internos
        # barrados já na saída), depois a lista de permitidos.
        self._validate_address(host)
        self._validate_host(host)

    def _validate_scheme(self, parts) -> None:

        # `or ""`: URL sem esquema (`//host/x`) tem `scheme` vazio, e o
        # `None` do urlsplit estouraria na comparação. A mensagem trata
        # os dois casos com `<ausente>`.
        scheme = (parts.scheme or "").lower()

        if scheme not in self.allowed_schemes:

            raise SecurityException(
                f"Esquema '{scheme or '<ausente>'}' não permitido; "
                f"esperado: {sorted(self.allowed_schemes)}.",
                code=self.DISALLOWED_SCHEME
            )

    def _validate_credentials(self, parts) -> None:

        # Credencial embutida na URL (`http://user:senha@host`) é
        # vazamento garantido: ela aparece em log, em histórico e em
        # mensagem de erro.
        if parts.username or parts.password:

            raise SecurityException(
                "A URL não pode carregar credenciais.",
                code=self.URL_CREDENTIALS
            )

    def _host(self, parts) -> str:

        host = (parts.hostname or "").lower()

        if not host:

            raise SecurityException(
                "A URL não informa o host.",
                code=self.INVALID_URL
            )

        return host

    def _validate_address(self, host: str) -> None:
        """
        Barra IP LITERAL que não seja público.
        """

        # `ip_address` só aceita IP LITERAL. `ValueError` é a resposta
        # comum — a maioria dos hosts é NOME, e nome não é resolvido
        # nesta checagem (ver o docstring da classe).
        try:
            address = ip_address(host)
        except ValueError:
            return

        # `is_global` é falso para loopback, rede privada,
        # link-local (169.254.0.0/16), reservado e multicast.
        if not address.is_global:

            raise SecurityException(
                f"O endereço '{host}' é interno e não pode ser "
                f"alcançado por requisição externa.",
                code=self.PRIVATE_ADDRESS
            )

    def _validate_host(self, host: str) -> None:

        # Sem lista configurada, esta checagem não se aplica — e é isso
        # que o `None` distingue de lista vazia.
        if self.allowed_hosts is None:
            return

        if self._matches_host(host):
            return

        raise SecurityException(
            f"O host '{host}' não está na lista de permitidos.",
            code=self.DISALLOWED_HOST
        )

    def _matches_host(self, host: str) -> bool:
        """
        Casa o host exato ou um subdomínio dele.
        """

        # `==` OU sufixo com PONTO: `api.exemplo.com` casa com
        # `exemplo.com` (subdomínio), mas `naoexemplo.com` NÃO casa — é
        # o ponto no `f".{allowed}"` que separa os dois casos.
        return any(
            host == allowed or host.endswith(f".{allowed}")
            for allowed in self.allowed_hosts
        )
