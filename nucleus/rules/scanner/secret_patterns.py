import re

# Padrões de segredos CONHECIDOS.
#
# Diferente da SOLAR-SEG-001 (que casa pelo NOME — SECRET_KEY,
# password, ...), aqui o segredo é reconhecido pelo PRÓPRIO
# CONTEÚDO, independentemente do nome que recebeu:
#
#     CHAVE = "AKIAIOSFODNN7EXAMPLE"      ← parece inofensivo
#
# Cada padrão tem um NOME para a mensagem (o valor NUNCA é
# armazenado nem ecoado).
SECRET_PATTERNS = (
    (
        "private-key",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
    ),
    (
        "aws-access-key",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
    ),
    (
        "github-token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")
    ),
    (
        "slack-token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")
    ),
    (
        "stripe-key",
        re.compile(r"\bsk_live_[A-Za-z0-9]{10,}")
    ),
    (
        "google-api-key",
        re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")
    ),
    (
        "jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_\-]{10,}"
            r"\.[A-Za-z0-9_\-]{10,}"
            r"\.[A-Za-z0-9_\-]{10,}"
        )
    ),
)

# Marcadores de VALOR DE EXEMPLO.
#
# Um casamento de padrão não prova que o valor é uma credencial
# real. A documentação dos próprios fornecedores usa chaves de
# exemplo (a AWS publica "AKIAIOSFODNN7EXAMPLE"), e quem escreve
# teste/parser precisa de dados falsos.
#
# Sem isso, a regra reprova arquivo que não tem segredo nenhum —
# e a reação natural é desligar a regra.
#
# É uma ALLOWLIST FECHADA e explícita: só entra aqui o que
# claramente se declara exemplo. A comparação é feita em
# MAIÚSCULAS, então "example", "Example" e "EXAMPLE" casam.
PLACEHOLDER_MARKERS = (
    "EXAMPLE",
    "EXEMPLO",
    "FAKE",
    "FALSO",
    "FALSA",
    "DUMMY",
    "PLACEHOLDER",
    "CHANGEME",
    "CHANGE_ME",
    "SAMPLE",
    "YOUR_",
    "XXXX",
    "TODO",
)

# Prefixo de valor DEFAULT.
#
# Convenção do projeto: um valor que COMEÇA com este prefixo é a
# marca de "campo vazio, o valor real vem do ambiente":
#
#     DATABASE_PASSWORD = "SOLAR_DEFAULT"
#
# O prefixo é configurável — troque-o aqui se o projeto usar outro.
PLACEHOLDER_PREFIX = "SOLAR_DEFAULT"


def match_secret(value: str) -> str | None:
    """
    Retorna o NOME do padrão que casou, ou None.

    O valor analisado nunca é devolvido nem registrado.
    """

    for name, pattern in SECRET_PATTERNS:

        if pattern.search(value):
            return name

    return None


def is_example(value: str) -> bool:
    """
    Indica se o valor é um EXEMPLO/PLACEHOLDER conhecido.

    Estes valores são legítimos no código-fonte: são justamente o
    que a documentação dos fornecedores e os testes usam.

    O valor marcado como DEFAULT (começa com o prefixo) também
    entra aqui: está dito no código que ele espera vir do
    ambiente.
    """

    if value.startswith(PLACEHOLDER_PREFIX):
        return True

    upper = value.upper()

    return any(
        marker in upper
        for marker in PLACEHOLDER_MARKERS
    )
