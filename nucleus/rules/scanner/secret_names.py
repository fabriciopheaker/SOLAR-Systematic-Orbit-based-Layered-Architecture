import re

# Vocabulário de nomes SENSÍVEIS da SOLAR.
#
# A comparação é por SUFIXO e ignora separadores, para casar as
# variações reais de nomenclatura sem gerar falso positivo:
#
#     DATABASE_PASSWORD → "databasepassword" → ✅
#     USER_PASSWORD     → "userpassword"     → ✅
#     SECRET_KEY        → "secretkey"        → ✅
#     csrf_token        → "csrftoken"        → ✅
#     PASSWORD_HASH     → "passwordhash"     → ✅ (composto explícito)
#     password_field    → "passwordfield"    → ❌ (é rótulo)
#     TOKEN_EXPIRATION  → "tokenexpiration"  → ❌ (não é o token)
SECRET_TOKENS = (
    "password",
    "passwd",
    "pwd",
    "senha",
    "secret",
    "secretkey",
    "token",
    "apikey",
    "accesskey",
    "privatekey",
    "credential",
    "credentials",
    "dbpass",
    "databasepassword",
    # Compostos em que o qualificador vem DEPOIS do token, e por
    # isso a comparação por sufixo não alcança:
    "passwordhash",
    "passworddigest",
    "hashedpassword",
)


def normalize(name: str) -> str:
    """
    Normaliza um nome para comparação: minúsculo, sem separadores.

        DATABASE_PASSWORD → "databasepassword"
        secret-key        → "secretkey"
    """

    return re.sub(r"[^a-z0-9]", "", name.lower())


def is_secret_name(name: str) -> bool:
    """
    Indica se um nome (variável, chave, atributo) é SENSÍVEL.

    Um nome é sensível quando é igual a um dos tokens de segredo
    ou TERMINA com um deles.
    """

    normalized = normalize(name)

    if not normalized:
        return False

    return any(
        normalized == token or normalized.endswith(token)
        for token in SECRET_TOKENS
    )
