# SOLAR-SEG-010 — SSRF: quem chama não escolhe o destino.
#
# A regra decide por NOME (`request.names`), e não por fluxo de dados:
# sem análise de taint, uma URL "lavada" por várias funções não é
# rastreável. Por isso o limite fica documentado no docstring da
# classe, e o instrumento para os casos legítimos é o `UrlGuard`.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import SECURITY, Rule, rule_code
from nucleus.rules.scanner.outbound_request import OutboundRequest


class OutboundRequestsMustNotUseUntrustedUrl(Rule):
    """
    Regra arquitetural:

    SOLAR-SEG-010

    Chamadas a serviços externos NÃO podem usar URL não confiável
    (SSRF — Server-Side Request Forgery).

    Se quem chama escolhe o destino, ele escolhe o que a
    aplicação acessa — inclusive a rede interna:

        # requisição maliciosa
        GET /preview?url=http://169.254.169.254/latest/meta-data/

        requests.get(request.args["url"])        ❌ credenciais
                                                    da instância
        httpx.get(f"http://{host}/health")       ❌ rede interna
        requests.get(url)                        ❌ o que vier

    É VIOLAÇÃO:

        requests.get(request.args["url"])           ❌
        httpx.get(f"http://{host}/internal")        ❌
        requests.get(callback_url)                  ❌
        session.get(self.next_url)                  ❌

    Correto:

        requests.get("https://api.exemplo.com/users")   ✅
        requests.get(f"{BASE_URL}/users")               ✅
        requests.get(environment.get("API_URL"))        ✅

    O critério é o ORIGEM da URL, pela convenção do projeto:

        CONSTANTE   identificador em UPPER_CASE (API_URL,
                    BASE_URL) — o valor foi decidido no código;
        CONFIGURAÇÃO nomes do vocabulário CONFIGURATION_NAMES
                    (environment, settings, config...) — o valor
                    foi decidido na configuração.

    Qualquer outro identificador que componha a URL é tratado
    como NÃO confiável.

    Para os casos que precisam mesmo variar em tempo de execução,
    o instrumento é `nucleus.security.url_guard.UrlGuard`, que
    restringe esquema, host e endereços internos antes da chamada.

    Limitação documentada: a decisão é por NOME, não por fluxo de
    dados — sem análise de taint, uma URL "lavada" por várias
    funções não é rastreável.

    O contexto desta regra é um OutboundRequest.
    """

    # Vocabulário de ORIGEM DE CONFIGURAÇÃO.
    CONFIGURATION_NAMES = frozenset({
        "conf",
        "config",
        "configuration",
        "environ",
        "environment",
        "getenv",
        "settings",
    })

    def code(self) -> str:
        return rule_code(SECURITY, 10)

    def description(self) -> str:
        return (
            "Chamadas a serviços externos não podem usar URL não "
            "confiável (SSRF)."
        )

    def validate(self, request: OutboundRequest) -> None:

        # Recolhe TODOS os nomes não confiáveis: uma chamada com dois
        # identificadores suspeitos é reportada uma vez só, com os
        # dois na mensagem.
        untrusted = self._untrusted(request)

        if not untrusted:
            return

        raise SolarException(
            self._build_message(request, untrusted)
        )

    def _untrusted(self, request: OutboundRequest) -> list[str]:

        # `sorted` porque `names` é conjunto: sem ordem fixa, o mesmo
        # achado sairia com os nomes trocados de posição a cada
        # execução.
        return sorted(
            name
            for name in request.names
            if not self._is_trusted(name)
        )

    def _is_trusted(self, name: str) -> bool:
        """
        Indica se o identificador é origem confiável de URL.
        """

        # Constante: pela convenção do projeto, UPPER_CASE.
        # `len(name) > 1` descarta o nome de UMA letra só — que
        # `isupper()` aceitaria sem ser constante nenhuma.
        if len(name) > 1 and name.isupper():
            return True

        # Configuração: comparação em minúsculas, porque `Environment`
        # e `environment` são o mesmo vocabulário para quem lê.
        return name.lower() in self.CONFIGURATION_NAMES

    def _build_message(
        self,
        request: OutboundRequest,
        untrusted: list[str]
    ) -> str:

        names = ", ".join(f"'{name}'" for name in untrusted)

        return (
            f"{self.code()}: {request.package} recebe URL montada "
            f"com {names} em {request.file}:{request.line}. "
            f"Uma URL escolhida por quem chama permite alcançar a "
            f"rede interna. Use constante, configuração ou valide "
            f"com UrlGuard antes da chamada."
        )
