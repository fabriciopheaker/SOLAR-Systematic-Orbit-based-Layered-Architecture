from nucleus.rules.scanner.token_security_scanner import (
    TokenSecurityScanner
)


INSECURE = """
import jwt

token = jwt.encode({"sub": "1"}, key, algorithm="none")

data = jwt.decode(token, key, options={"verify_signature": False})
"""

WITHOUT_EXPIRATION = """
import jwt

token = jwt.encode({"sub": "1"}, key, algorithm="HS256")
"""

SECURE = """
import jwt

token = jwt.encode(
    {"sub": "1", "exp": expires_at},
    key,
    algorithm="HS256"
)

data = jwt.decode(token, key, algorithms=["HS256"])
"""

NAMESPACED = """
import jose

token = jose.jwt.encode({"sub": "1"}, key, algorithm="none")
"""


def _scan(tmp_path, content: str):

    path = tmp_path / "token_gateway.py"
    path.write_text(content, encoding="utf-8")

    return TokenSecurityScanner(tmp_path).scan()


def test_scanner_describes_insecure_usage(tmp_path):

    usages = _scan(tmp_path, INSECURE)

    assert len(usages) == 2

    encode = usages[0]
    decode = usages[1]

    assert encode.operation == "encode"
    assert encode.algorithm == "none"
    assert encode.has_expiration is False

    assert decode.operation == "decode"
    assert decode.verifies_signature is False
    assert decode.algorithm is None


def test_scanner_detects_missing_expiration(tmp_path):

    usage = _scan(tmp_path, WITHOUT_EXPIRATION)[0]

    assert usage.algorithm == "HS256"
    assert usage.has_expiration is False


def test_scanner_describes_secure_usage(tmp_path):

    usages = _scan(tmp_path, SECURE)

    encode, decode = usages

    assert encode.algorithm == "HS256"
    assert encode.has_expiration is True
    assert encode.verifies_signature is None

    assert decode.algorithm == "HS256"
    assert decode.verifies_signature is None


# jwt dentro de outro namespace tambem e reconhecido
def test_scanner_recognizes_namespaced_jwt(tmp_path):

    usage = _scan(tmp_path, NAMESPACED)[0]

    assert usage.operation == "encode"
    assert usage.algorithm == "none"


def test_scanner_without_tokens_returns_empty(tmp_path):

    path = tmp_path / "service.py"
    path.write_text("VALUE = 1\n", encoding="utf-8")

    assert TokenSecurityScanner(tmp_path).scan() == []
