import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.models_must_live_in_their_own_file import (
    ModelsMustLiveInTheirOwnFile
)
from nucleus.rules.scanner.module_classes import (
    DeclaredClass,
    ModuleClasses,
)


def _module(
    classes: list[tuple[str, int]],
    module: str = "orbits.database.models.entities",
    file: str = "orbits/database/models/entities.py"
) -> ModuleClasses:

    return ModuleClasses(
        module=module,
        file=file,
        classes=tuple(
            DeclaredClass(name=name, line=line)
            for name, line in classes
        )
    )


# ---------------------------------------------------------------------
# Violações
# ---------------------------------------------------------------------

# dois Models no mesmo arquivo
def test_two_models_in_one_file_are_rejected():

    rule = ModelsMustLiveInTheirOwnFile()

    with pytest.raises(SolarException):
        rule.validate(
            _module([
                ("UserModel", 1),
                ("DocumentModel", 10),
            ])
        )


# o LUGAR basta: dentro de models/ tudo e Model
def test_models_segment_makes_any_class_a_model():

    rule = ModelsMustLiveInTheirOwnFile()

    with pytest.raises(SolarException):
        rule.validate(
            _module([
                ("User", 1),
                ("Document", 20),
            ])
        )


# o NOME basta: fora de models/ tambem vale
def test_model_suffix_outside_the_models_layer_is_rejected():

    rule = ModelsMustLiveInTheirOwnFile()

    with pytest.raises(SolarException):
        rule.validate(
            _module(
                classes=[
                    ("UserModel", 3),
                    ("DocumentModel", 40),
                ],
                module="planets.documents.entities",
                file="planets/documents/entities.py"
            )
        )


# o nome do MODULO tambem identifica o Model, como nas regras 005/006
# (mesmo com classes que nao terminam em "Model")
def test_model_module_name_identifies_the_layer():

    rule = ModelsMustLiveInTheirOwnFile()

    with pytest.raises(SolarException):
        rule.validate(
            _module(
                classes=[
                    ("User", 3),
                    ("Document", 40),
                ],
                module="planets.documents.document_model",
                file="planets/documents/document_model.py"
            )
        )


def test_three_models_are_all_listed():

    rule = ModelsMustLiveInTheirOwnFile()

    with pytest.raises(SolarException) as error:
        rule.validate(
            _module([
                ("UserModel", 1),
                ("DocumentModel", 10),
                ("ProjectModel", 20),
            ])
        )

    message = str(error.value)

    assert "3 Models" in message
    assert "ProjectModel (linha 20)" in message


# ---------------------------------------------------------------------
# Permitido
# ---------------------------------------------------------------------

def test_one_model_per_file_is_allowed():

    rule = ModelsMustLiveInTheirOwnFile()

    rule.validate(_module([("UserModel", 1)]))


# classe que nao e Model nao entra na contagem
def test_non_model_classes_are_not_counted():

    rule = ModelsMustLiveInTheirOwnFile()

    rule.validate(
        _module(
            classes=[
                ("UserResource", 1),
                ("DocumentResource", 20),
            ],
            module="planets.documents.resources",
            file="planets/documents/resources.py"
        )
    )


# um Model + classes que nao sao Models continua valendo: so
# contam os Models
def test_one_model_beside_other_classes_is_allowed():

    rule = ModelsMustLiveInTheirOwnFile()

    rule.validate(
        _module(
            classes=[
                ("UserModel", 1),
                ("UserResource", 20),
                ("UserValidator", 40),
            ],
            module="planets.users.entities",
            file="planets/users/entities.py"
        )
    )


def test_file_without_classes_is_allowed():

    rule = ModelsMustLiveInTheirOwnFile()

    rule.validate(_module([], module="orbits.database.models.base"))


# ---------------------------------------------------------------------
# Mensagem
# ---------------------------------------------------------------------

def test_message_points_to_the_file_and_the_models():

    rule = ModelsMustLiveInTheirOwnFile()

    with pytest.raises(SolarException) as error:
        rule.validate(
            _module([
                ("UserModel", 1),
                ("DocumentModel", 10),
            ])
        )

    message = str(error.value)

    assert "SOLAR-ARCH-032" in message
    assert "orbits/database/models/entities.py" in message
    assert "UserModel (linha 1)" in message
    assert "DocumentModel (linha 10)" in message
    assert "user_model.py" in message
