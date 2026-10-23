import pytest

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.architecture.controller_and_usecase_must_use_named_contracts import (
    ControllerAndUseCaseMustUseNamedContracts
)
from nucleus.contracts.responsibility_contract import ResponsibilityContract


class CreateUserInput:
    pass


class UserOutput:
    pass


class ListUsersInput:
    pass


class ListUsersOutput:
    pass


# contratos nomeados que HERDAM de coleções continuam válidos:
# a arquitetura reconhece UserInput/UsersOutput como contratos.
class UserInput(dict):
    pass


class UsersOutput(list):
    pass


# contrato de entrada anonimo (dict) e invalido
def test_anonymous_input_contract_is_invalid():

    contract = ResponsibilityContract(
        owner="UserController.store",
        input_type=dict,
        output_type=UserOutput
    )

    rule = ControllerAndUseCaseMustUseNamedContracts()

    with pytest.raises(SolarException):
        rule.validate(contract)


# contrato de saida anonimo (list) e invalido
def test_anonymous_output_contract_is_invalid():

    contract = ResponsibilityContract(
        owner="CreateUserUseCase.execute",
        input_type=CreateUserInput,
        output_type=list
    )

    rule = ControllerAndUseCaseMustUseNamedContracts()

    with pytest.raises(SolarException):
        rule.validate(contract)


# anotacao de texto anonima ("dict") e invalida
def test_text_annotation_anonymous_contract_is_invalid():

    contract = ResponsibilityContract(
        owner="UserController.store",
        input_type="dict",
        output_type=UserOutput
    )

    rule = ControllerAndUseCaseMustUseNamedContracts()

    with pytest.raises(SolarException):
        rule.validate(contract)


# generico anotado ("typing.List[UserOutput]") tambem e contrato anonimo
def test_generic_text_annotation_contract_is_invalid():

    contract = ResponsibilityContract(
        owner="ListUsersUseCase.execute",
        input_type=ListUsersInput,
        output_type="typing.List[UserOutput]"
    )

    rule = ControllerAndUseCaseMustUseNamedContracts()

    with pytest.raises(SolarException):
        rule.validate(contract)


# entrada e saida anonimas no mesmo contrato
def test_both_anonymous_contracts_are_invalid():

    contract = ResponsibilityContract(
        owner="UserController.index",
        input_type=dict,
        output_type=list
    )

    rule = ControllerAndUseCaseMustUseNamedContracts()

    with pytest.raises(SolarException):
        rule.validate(contract)


# built-in generic literal (dict[str, int]) e anonimo
def test_builtin_generic_literal_is_invalid():

    contract = ResponsibilityContract(
        owner="UserController.store",
        input_type=dict[str, int],
        output_type=UserOutput
    )

    rule = ControllerAndUseCaseMustUseNamedContracts()

    with pytest.raises(SolarException):
        rule.validate(contract)


# contrato anonimo aninhado em anotacao (Optional[dict]) e invalido
def test_nested_anonymous_annotation_is_invalid():

    contract = ResponsibilityContract(
        owner="UserController.store",
        input_type=ListUsersInput,
        output_type="typing.Optional[dict]"
    )

    rule = ControllerAndUseCaseMustUseNamedContracts()

    with pytest.raises(SolarException):
        rule.validate(contract)


# contratos nomeados sao validos
def test_named_contracts_are_valid():

    contract = ResponsibilityContract(
        owner="UserController.store",
        input_type=CreateUserInput,
        output_type=UserOutput
    )

    rule = ControllerAndUseCaseMustUseNamedContracts()

    rule.validate(contract)


# contratos nao declarados nao violam a regra
def test_missing_contracts_do_not_violate():

    contract = ResponsibilityContract(owner="UserController.store")

    rule = ControllerAndUseCaseMustUseNamedContracts()

    rule.validate(contract)


# contrato NOMEADO que herda de dict/list continua valido
def test_named_subclass_of_collection_is_valid():

    contract = ResponsibilityContract(
        owner="UserController.store",
        input_type=UserInput,
        output_type=UsersOutput
    )

    rule = ControllerAndUseCaseMustUseNamedContracts()

    rule.validate(contract)


# ESCOPO: uso INTERNO de colecoes (loop, agregacao, indexacao) nao
# e violacao. A regra so enxerga o contrato declarado, nunca o
# corpo do metodo — por isso um UseCase que itera sobre listas e
# usa dicts internamente continua valido.
def test_internal_collections_are_not_part_of_the_contract():

    contract = ResponsibilityContract(
        owner="ListUsersUseCase.execute",
        input_type=ListUsersInput,
        output_type=ListUsersOutput
    )

    rule = ControllerAndUseCaseMustUseNamedContracts()

    rule.validate(contract)
