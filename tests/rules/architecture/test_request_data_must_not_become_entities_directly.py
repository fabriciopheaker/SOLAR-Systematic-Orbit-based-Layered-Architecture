import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.request_data_must_not_become_entities_directly import (
    RequestDataMustNotBecomeEntitiesDirectly
)
from nucleus.rules.scanner.entity_binding import EntityBinding


def _binding(
    source: str = "request.json",
    target: str = "DocumentEntity",
    kind: str = "expansion"
) -> EntityBinding:

    return EntityBinding(
        target=target,
        source=source,
        kind=kind,
        file="orbits/planets/documents/controllers/document_controller.py",
        line=18
    )


# ---------------------------------------------------------------------
# Violações
# ---------------------------------------------------------------------

# o request inteiro virando Entity e mass assignment
def test_request_json_expansion_is_rejected():

    rule = RequestDataMustNotBecomeEntitiesDirectly()

    with pytest.raises(SolarException):
        rule.validate(_binding())


# variavel crua tambem: nao se sabe o que carrega
def test_raw_variable_source_is_rejected():

    rule = RequestDataMustNotBecomeEntitiesDirectly()

    with pytest.raises(SolarException):
        rule.validate(_binding(source="payload"))


def test_update_with_expansion_is_rejected():

    rule = RequestDataMustNotBecomeEntitiesDirectly()

    with pytest.raises(SolarException):
        rule.validate(
            _binding(
                source="request.json",
                target="Model.query",
                kind="update"
            )
        )


def test_from_dict_is_rejected():

    rule = RequestDataMustNotBecomeEntitiesDirectly()

    with pytest.raises(SolarException):
        rule.validate(_binding(kind="mapping"))


# ---------------------------------------------------------------------
# Permitido
# ---------------------------------------------------------------------

# o Input filtra: o cliente nao escolhe quais campos entram
def test_input_contract_is_allowed():

    rule = RequestDataMustNotBecomeEntitiesDirectly()

    rule.validate(_binding(source="DocumentInput"))


# dicionario literal: os campos estao a vista
def test_dict_literal_is_allowed():

    rule = RequestDataMustNotBecomeEntitiesDirectly()

    rule.validate(_binding(source="{}"))


# ---------------------------------------------------------------------
# setattr em laço
# ---------------------------------------------------------------------

# so e violacao quando a origem se declara da requisicao
def test_setattr_over_request_data_is_rejected():

    rule = RequestDataMustNotBecomeEntitiesDirectly()

    with pytest.raises(SolarException):
        rule.validate(
            _binding(
                source="payload.items",
                target="document",
                kind="setattr"
            )
        )


# um laco sobre configuracao nao tem nada a ver com mass assignment
def test_setattr_over_configuration_is_allowed():

    rule = RequestDataMustNotBecomeEntitiesDirectly()

    rule.validate(
        _binding(
            source="config.items",
            target="self",
            kind="setattr"
        )
    )


# ---------------------------------------------------------------------
# Mensagem
# ---------------------------------------------------------------------

def test_message_explains_the_fix():

    rule = RequestDataMustNotBecomeEntitiesDirectly()

    with pytest.raises(SolarException) as error:
        rule.validate(_binding())

    message = str(error.value)

    assert "SOLAR-ARCH-029" in message
    assert "request.json" in message
    assert "DocumentEntity" in message
    assert "document_controller.py:18" in message
    assert "Input" in message
