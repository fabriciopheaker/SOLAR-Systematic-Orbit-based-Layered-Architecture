import pytest

from nucleus.exceptions.validation_exception import ValidationException
from nucleus.security.json_sanitizer import JsonSanitizer
from nucleus.security.json_validator import JsonValidator


# ---------------------------------------------------------------------
# Sanitizer
# ---------------------------------------------------------------------

# espaco em volta de texto e ruido de digitacao: "  Ana  " e "Ana"
# sao o mesmo nome
def test_sanitizer_trims_text():

    assert JsonSanitizer().sanitize({"name": "  Ana  "}) == {"name": "Ana"}


# chave sem valor nao vira campo: None e a ausencia escrita de outra
# forma
def test_sanitizer_drops_the_key_without_value():

    sanitized = JsonSanitizer().sanitize({"name": "Ana", "apelido": None})

    assert sanitized == {"name": "Ana"}


# numero e booleano NAO tem espaco em volta, e chamar strip neles
# estouraria
def test_sanitizer_keeps_the_other_types():

    payload = {"idade": 30, "ativo": True}

    assert JsonSanitizer().sanitize(payload) == payload


# o corpo recebido NAO muda: quem chamou ainda tem a referencia dele
def test_sanitizer_does_not_touch_the_payload():

    payload = {"name": "  Ana  "}

    JsonSanitizer().sanitize(payload)

    assert payload == {"name": "  Ana  "}


# corpo que nao e objeto JSON nao tem o que normalizar
def test_sanitizer_rejects_a_body_that_is_not_an_object():

    with pytest.raises(ValidationException) as caught:
        JsonSanitizer().sanitize(["nao", "e", "objeto"])

    assert caught.value.code == "INVALID_JSON_BODY"


# ---------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------

def test_validator_accepts_when_every_required_field_is_present():

    validator = JsonValidator(required=("name", "email"))

    validator.validate({"name": "Ana", "email": "ana@exemplo.com"})


# os TRES casos sao o mesmo problema para quem consome o dado, e os
# tres acusam
@pytest.mark.parametrize("payload", [
    {"email": "ana@exemplo.com"},
    {"name": None, "email": "ana@exemplo.com"},
    {"name": "   ", "email": "ana@exemplo.com"},
])
def test_validator_rejects_a_required_field_without_value(payload):

    validator = JsonValidator(required=("name", "email"))

    with pytest.raises(ValidationException) as caught:
        validator.validate(payload)

    assert caught.value.code == "MISSING_FIELDS"


# todos os campos que faltam vem na MESMA recusa: corrigir um por vez
# obrigaria a rodar de novo para descobrir o proximo
def test_validator_reports_every_missing_field_at_once():

    validator = JsonValidator(required=("name", "email", "senha"))

    with pytest.raises(ValidationException) as caught:
        validator.validate({})

    message = str(caught.value)

    assert "name" in message
    assert "email" in message
    assert "senha" in message


# campo NAO exigido nao atrapalha
def test_validator_ignores_the_fields_it_does_not_require():

    validator = JsonValidator(required=("name",))

    validator.validate({"name": "Ana", "extra": 1})


def test_validator_rejects_a_body_that_is_not_an_object():

    validator = JsonValidator(required=("name",))

    with pytest.raises(ValidationException) as caught:
        validator.validate("texto solto")

    assert caught.value.code == "INVALID_JSON_BODY"
