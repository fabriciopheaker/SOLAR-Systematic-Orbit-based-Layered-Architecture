from nucleus.rules.scanner.secret_content_scanner import (
    SUPPRESSION_MARKER,
    SecretContentScanner
)


# Chave com formato de credencial REAL: casa o padrão da AWS e não
# contém nenhum marcador de exemplo.
REAL_KEY = "AKIA2B3C4D5E6F7G8H9J"

# Chave que a própria AWS publica como exemplo na documentação.
EXAMPLE_KEY = "AKIAIOSFODNN7EXAMPLE"

PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----"

JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abcdefghijk"

WITH_SECRETS = (
    f'CHAVE = "{REAL_KEY}"\n'
    f'HEADER = "{PRIVATE_KEY}"\n'
    f'TOKEN = "{JWT}"\n'
)


def _scan(tmp_path, name: str, content: str):
    """
    Escreve o conteúdo em um arquivo e devolve as ocorrências.
    """

    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return SecretContentScanner(tmp_path).scan()

FROM_ENVIRONMENT = """
import os

CHAVE = os.environ["AWS_ACCESS_KEY_ID"]
TOKEN = environment.get("API_TOKEN")
"""


# ---------------------------------------------------------------------
# Detecção por CONTEÚDO
# ---------------------------------------------------------------------

def test_scanner_finds_secret_by_content(tmp_path):

    patterns = sorted(
        finding.pattern
        for finding in _scan(tmp_path, "config.py", WITH_SECRETS)
    )

    assert patterns == ["aws-access-key", "jwt", "private-key"]


# o VALOR nunca e armazenado (evita transformar o relatorio
# em um novo vazamento)
def test_scanner_does_not_store_the_secret_value(tmp_path):

    finding = _scan(tmp_path, "config.py", WITH_SECRETS)[0]

    assert not hasattr(finding, "value")


def test_scanner_ignores_values_from_environment(tmp_path):

    assert _scan(tmp_path, "config.py", FROM_ENVIRONMENT) == []


def test_scanner_returns_empty_without_files(tmp_path):

    assert SecretContentScanner(tmp_path).scan() == []


# ---------------------------------------------------------------------
# (A) Diretórios sem código de produção ficam de fora
# ---------------------------------------------------------------------

def test_scanner_skips_test_directories(tmp_path):

    content = f'CHAVE = "{REAL_KEY}"\n'

    assert _scan(tmp_path, "tests/config.py", content) == []
    assert _scan(tmp_path, "fixtures/config.py", content) == []
    assert _scan(tmp_path, "examples/config.py", content) == []


# so o DIRETORIO conta: um arquivo chamado tests.py e codigo normal
def test_scanner_does_not_skip_a_file_named_like_a_test(tmp_path):

    findings = _scan(tmp_path, "tests.py", f'CHAVE = "{REAL_KEY}"\n')

    assert len(findings) == 1


# a exclusao e configuravel
def test_scanner_accepts_custom_excluded_directories(tmp_path):

    path = tmp_path / "tests"
    path.mkdir()
    (path / "config.py").write_text(
        f'CHAVE = "{REAL_KEY}"\n',
        encoding="utf-8"
    )

    scanner = SecretContentScanner(
        tmp_path,
        excluded_directories=set()
    )

    assert len(scanner.scan()) == 1


# ---------------------------------------------------------------------
# (B) Marcador explícito de exceção
# ---------------------------------------------------------------------

def test_marker_on_the_same_line_suppresses(tmp_path):

    content = f'CHAVE = "{REAL_KEY}"  # {SUPPRESSION_MARKER}\n'

    finding = _scan(tmp_path, "config.py", content)[0]

    assert finding.suppressed is True


def test_comment_above_suppresses(tmp_path):

    content = f'# {SUPPRESSION_MARKER}\nCHAVE = "{REAL_KEY}"\n'

    finding = _scan(tmp_path, "config.py", content)[0]

    assert finding.suppressed is True


def test_marker_inside_multiline_literal_suppresses(tmp_path):

    content = (
        "CHAVE = (\n"
        f"    # {SUPPRESSION_MARKER}\n"
        f'    "{REAL_KEY}"\n'
        ")\n"
    )

    finding = _scan(tmp_path, "config.py", content)[0]

    assert finding.suppressed is True


# o marcador NAO libera a linha seguinte quando esta no fim de uma
# instrucao qualquer (senao viraria um ignore escondido)
def test_marker_at_the_end_of_other_code_does_not_suppress(tmp_path):

    content = (
        f"OUTRA = 1  # {SUPPRESSION_MARKER}\n"
        f'CHAVE = "{REAL_KEY}"\n'
    )

    occurrences = _scan(tmp_path, "config.py", content)

    key = [item for item in occurrences if item.line == 2][0]

    assert key.suppressed is False


def test_secret_without_marker_is_not_suppressed(tmp_path):

    finding = _scan(tmp_path, "config.py", f'CHAVE = "{REAL_KEY}"\n')[0]

    assert finding.suppressed is False


# ---------------------------------------------------------------------
# (C) Valores de exemplo/placeholder conhecidos
# ---------------------------------------------------------------------

def test_scanner_flags_known_example_values(tmp_path):

    finding = _scan(tmp_path, "config.py", f'CHAVE = "{EXAMPLE_KEY}"\n')[0]

    assert finding.pattern == "aws-access-key"
    assert finding.example is True


# a comparacao e feita em MAIUSCULAS
# (a ocorrencia e marcada, mas ainda e reportada)
def test_example_detection_ignores_case(tmp_path):

    finding = _scan(
        tmp_path,
        "config.py",
        f'CHAVE = "{REAL_KEY}-example"\n'
    )[0]

    assert finding.example is True


# valor com formato de credencial real nao e tratado como exemplo
def test_real_looking_value_is_not_an_example(tmp_path):

    finding = _scan(tmp_path, "config.py", f'CHAVE = "{REAL_KEY}"\n')[0]

    assert finding.example is False


# ---------------------------------------------------------------------
# (D) Blocos de documentação
# ---------------------------------------------------------------------

def test_module_docstring_is_documentation(tmp_path):

    finding = _scan(
        tmp_path,
        "config.py",
        f'"""{PRIVATE_KEY}"""\n'
    )[0]

    assert finding.documentation is True


def test_function_docstring_is_documentation(tmp_path):

    content = (
        "def montar():\n"
        f'    """{PRIVATE_KEY}"""\n'
        "    return 1\n"
    )

    finding = _scan(tmp_path, "config.py", content)[0]

    assert finding.documentation is True


def test_loose_text_block_is_documentation(tmp_path):

    content = f'"""\n{PRIVATE_KEY}\n"""\n'

    finding = _scan(tmp_path, "config.py", content)[0]

    assert finding.documentation is True


# literal ATRIBUIDO e um valor de verdade, nao documentacao
def test_assigned_literal_is_not_documentation(tmp_path):

    finding = _scan(tmp_path, "config.py", f'CHAVE = "{REAL_KEY}"\n')[0]

    assert finding.documentation is False


# literal dentro de estrutura nao e documentacao
def test_literal_inside_structure_is_not_documentation(tmp_path):

    content = f'CHAVES = {{"aws": "{REAL_KEY}"}}\n'

    finding = _scan(tmp_path, "config.py", content)[0]

    assert finding.documentation is False


# um segredo DENTRO de docstring continua sendo reportado: quem
# decide ignorar e a Rule, nao o scanner
def test_secret_inside_docstring_is_still_reported(tmp_path):

    content = f'"""\n{PRIVATE_KEY}\n"""\n'

    assert len(_scan(tmp_path, "config.py", content)) == 1
