from pathlib import Path

import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.secrets_must_not_appear_in_source import (
    SecretsMustNotAppearInSource
)
from nucleus.rules.scanner.secret_content_scanner import (
    SecretContentScanner
)
from nucleus.rules.scanner.secret_occurrence import SecretOccurrence


def _occurrence(pattern: str, **justifications) -> SecretOccurrence:

    return SecretOccurrence(
        pattern=pattern,
        file="orbits/database/persistence/persistence.py",
        line=10,
        **justifications
    )


def _nucleus_root() -> Path:
    """
    Localiza o diretório nucleus/ do próprio projeto SOLAR.
    """

    for parent in Path(__file__).resolve().parents:

        candidate = parent / "nucleus"

        if candidate.is_dir():
            return candidate

    raise AssertionError("diretório nucleus/ não encontrado")


# segredo encontrado pelo conteudo viola a regra
def test_secret_in_source_is_rejected():

    rule = SecretsMustNotAppearInSource()

    with pytest.raises(SolarException):
        rule.validate(_occurrence("aws-access-key"))


# a mensagem NAO exibe o valor do segredo
def test_message_does_not_expose_the_value():

    rule = SecretsMustNotAppearInSource()

    with pytest.raises(SolarException) as error:
        rule.validate(_occurrence("jwt"))

    message = str(error.value)

    assert "jwt" in message
    assert "não é exibido" in message


# ---------------------------------------------------------------------
# Justificativas ignoradas por padrão
# ---------------------------------------------------------------------

# texto de documentação não é valor usado pelo programa
# (a própria regra descreve chaves de exemplo na sua docstring)
def test_documentation_is_ignored():

    rule = SecretsMustNotAppearInSource()

    rule.validate(_occurrence("private-key", documentation=True))


# valor de exemplo/placeholder conhecido não é credencial real
def test_example_is_ignored():

    rule = SecretsMustNotAppearInSource()

    rule.validate(_occurrence("aws-access-key", example=True))


# trecho anotado com "solar:allow-secret" é uma exceção explícita
def test_suppressed_is_ignored():

    rule = SecretsMustNotAppearInSource()

    rule.validate(_occurrence("aws-access-key", suppressed=True))


# ---------------------------------------------------------------------
# Modo estrito (para quem quiser a leitura literal da regra)
# ---------------------------------------------------------------------

def test_strict_mode_rejects_documentation():

    rule = SecretsMustNotAppearInSource(ignore_documentation=False)

    with pytest.raises(SolarException):
        rule.validate(_occurrence("private-key", documentation=True))


def test_strict_mode_rejects_examples():

    rule = SecretsMustNotAppearInSource(ignore_examples=False)

    with pytest.raises(SolarException):
        rule.validate(_occurrence("aws-access-key", example=True))


def test_strict_mode_rejects_suppressed():

    rule = SecretsMustNotAppearInSource(ignore_suppressed=False)

    with pytest.raises(SolarException):
        rule.validate(_occurrence("aws-access-key", suppressed=True))


# ---------------------------------------------------------------------
# Verificação de ponta a ponta no próprio código do SOLAR
# ---------------------------------------------------------------------

# a regra NÃO pode reprovar o próprio código: o que existe lá
# (docstrings citando exemplos de chave) é documentação, não segredo
# — se este teste falhar, aparecem na asserção os locais acusados
def test_rule_accepts_the_solar_source_tree():

    rule = SecretsMustNotAppearInSource()

    occurrences = SecretContentScanner(_nucleus_root()).scan()

    # a varredura precisa encontrar ALGO: as docstrings das próprias
    # regras citam chaves de exemplo. Se nada for encontrado, o teste
    # virou vazio e não prova nada.
    assert occurrences

    unjustified = []

    for occurrence in occurrences:

        try:
            rule.validate(occurrence)
        except SolarException:
            unjustified.append(occurrence)

    assert unjustified == []
