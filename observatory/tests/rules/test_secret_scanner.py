from nucleus.rules.scanner.secret_scanner import SecretScanner


HARDCODED = """
SECRET_KEY = "abc123"
DATABASE_PASSWORD = "root"
API_TOKEN: str = "987654"

connect(password="root")
"""

FROM_ENVIRONMENT = """
import os

SECRET_KEY = os.environ["SECRET_KEY"]
DATABASE_PASSWORD = environment.get("DB_PASS")
password = ""
"""

NOT_SECRETS = """
password_field = "senha"
TOKEN_EXPIRATION = "1h"
PASSWORD_MIN_LENGTH = "8"
"""

DEFAULTS = """
DATABASE_PASSWORD = "SOLAR_DEFAULT"
SECRET_KEY = "SOLAR_DEFAULT"
"""

SUPPRESSED = """
# solar:allow-secret (nome da chave no ambiente, não o valor)
SECRET_KEY = "SECRET_KEY"

INVALID_TOKEN = "INVALID_CSRF_TOKEN"  # solar:allow-secret
"""


def _scan(tmp_path, content: str):

    path = tmp_path / "config.py"
    path.write_text(content, encoding="utf-8")

    return SecretScanner(tmp_path).scan()


def test_scanner_finds_hardcoded_secrets(tmp_path):

    findings = _scan(tmp_path, HARDCODED)

    names = sorted(finding.name for finding in findings)

    assert names == [
        "API_TOKEN",
        "DATABASE_PASSWORD",
        "SECRET_KEY",
        "password",
    ]

    assert all(finding.file == "config.py" for finding in findings)
    assert all(finding.line > 0 for finding in findings)


def test_scanner_ignores_values_from_environment(tmp_path):

    assert _scan(tmp_path, FROM_ENVIRONMENT) == []


def test_scanner_ignores_names_that_are_not_secrets(tmp_path):

    assert _scan(tmp_path, NOT_SECRETS) == []


def test_scanner_returns_empty_without_files(tmp_path):

    assert SecretScanner(tmp_path).scan() == []


# valor marcado com o prefixo de DEFAULT nao e segredo
def test_scanner_marks_values_that_are_defaults(tmp_path):

    findings = _scan(tmp_path, DEFAULTS)

    assert len(findings) == 2
    assert all(finding.default is True for finding in findings)
    assert all(finding.suppressed is False for finding in findings)


# o marcador de excecao vale na propria linha e na linha de cima
def test_scanner_marks_suppressed_literals(tmp_path):

    findings = _scan(tmp_path, SUPPRESSED)

    assert len(findings) == 2
    assert all(finding.suppressed is True for finding in findings)
    assert all(finding.default is False for finding in findings)


# segredo de verdade nao tem marca nenhuma
def test_hardcoded_value_is_neither_default_nor_suppressed(tmp_path):

    finding = _scan(tmp_path, HARDCODED)[0]

    assert finding.default is False
    assert finding.suppressed is False


# o prefixo de DEFAULT e configuravel
def test_default_prefix_is_configurable(tmp_path):

    path = tmp_path / "config.py"
    path.write_text(
        'DATABASE_PASSWORD = "OUTRO_PREFIXO"\n',
        encoding="utf-8"
    )

    findings = SecretScanner(tmp_path, default_prefix="OUTRO").scan()

    assert findings[0].default is True


# a linha de cima so libera se for comentario DEDICADO
def test_marker_above_has_to_be_a_dedicated_comment(tmp_path):

    findings = _scan(
        tmp_path,
        'OUTRA = 1  # solar:allow-secret\nSECRET_KEY = "ABC"\n'
    )

    assert findings[0].suppressed is False
