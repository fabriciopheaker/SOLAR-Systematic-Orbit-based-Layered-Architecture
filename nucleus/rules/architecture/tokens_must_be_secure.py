# SOLAR-ARCH-027 — as três exigências do token.
#
# Os problemas são independentes e a regra acumula todos, em vez de
# parar no primeiro: corrigir `algorithm` e só então descobrir que
# faltava `exp` obrigaria a rodar o check de novo.
#
# O critério é sempre "VISTO errado", nunca "não sei" — ver
# `_problems`, que só acusa `False` explícito (o contexto guarda
# `None` para "não foi possível ver").
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import Rule
from nucleus.rules.scanner.token_usage import TokenUsage


class TokensMustBeSecure(Rule):
    """
    Regra arquitetural:

    SOLAR-ARCH-027

    JWT/Token seguro: todo token deve ser

        1. assinado com algoritmo EXPLÍCITO e seguro;
        2. VERIFICADO na leitura;
        3. emitido COM expiração.

    É VIOLAÇÃO:

        jwt.encode(payload, key, algorithm="none")              ❌
        jwt.encode(payload, key, algorithm="HS256")             ❌ (sem "exp")
        jwt.decode(token, key)                                  ❌ (algoritmo implícito)
        jwt.decode(token, key,
            options={"verify_signature": False})                ❌

    Correto:

        jwt.encode(
            {"sub": user_id, "exp": expires_at},
            key,
            algorithm="HS256",
        )                                                       ✅

        jwt.decode(token, key, algorithms=["HS256"])            ✅

    A chave de assinatura deve vir do Environment — a
    SOLAR-ARCH-020/023 cuidam disso.

    O contexto desta regra é um TokenUsage.
    """

    # Algoritmos que NÃO assinam o token.
    #
    # `"none"` é o algoritmo SEM ASSINATURA da própria especificação
    # do JWT — existe, e bibliotecas permissivas o aceitam; `""`
    # pega o caso de `algorithm=""`. A comparação é feita em
    # minúsculas por `strip().lower()` dentro de `_problems`.
    UNSAFE_ALGORITHMS = frozenset({
        "none",
        "",
    })

    def code(self) -> str:
        return "SOLAR-ARCH-027"

    def description(self) -> str:
        return (
            "JWT/Token deve ser assinado com algoritmo explícito, "
            "ter expiração e ser verificado na leitura."
        )

    def validate(self, usage: TokenUsage) -> None:

        problems = self._problems(usage)

        if not problems:
            return

        raise SolarException(
            self._build_message(usage, problems)
        )

    def _problems(self, usage: TokenUsage) -> list[str]:

        problems: list[str] = []

        # `if`/`elif`: algoritmo declarado só pode ter UM problema —
        # ou veio e está vazio/inseguro, ou veio e está bom. Não há
        # caso em que as duas condições se apliquem.
        if usage.algorithm is None:
            problems.append(
                "algoritmo não declarado explicitamente"
            )

        # `strip().lower()` porque `"NONE"`, `" none "` e `"none"`
        # são o mesmo algoritmo. Comparar cru deixaria passar a
        # variação de caixa — que é justamente o jeito de driblar
        # uma lista de proibidos.
        elif usage.algorithm.strip().lower() in self.UNSAFE_ALGORITHMS:
            problems.append(
                f"algoritmo inseguro '{usage.algorithm}'"
            )

        # `is False` e não `not usage.verifies_signature`: `None`
        # significa "não foi possível ver", e acusar a dúvida daria
        # falso positivo em verificação montada em tempo de execução.
        if usage.verifies_signature is False:
            problems.append(
                "verificação de assinatura desativada"
            )

        # Só na EMISSÃO: um token que apenas é LIDO não tem por que
        # declarar `exp` — quem responde por isso é quem o emitiu.
        if usage.operation == "encode" and usage.has_expiration is False:
            problems.append("token emitido sem expiração ('exp')")

        return problems

    def _build_message(
        self,
        usage: TokenUsage,
        problems: list[str]
    ) -> str:

        return (
            f"{self.code()}: "
            f"uso inseguro de token em {usage.operation} "
            f"({usage.file}:{usage.line}): "
            f"{'; '.join(problems)}. "
            f"Tokens devem ser assinados com algoritmo explícito, "
            f"ter expiração e ser verificados na leitura."
        )
