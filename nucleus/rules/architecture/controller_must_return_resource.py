# SOLAR-ROF-002 — Controller que devolve uma resposta sem passar por
# Resource.
#
# Regra de ANÁLISE ESTÁTICA: o contexto vem do
# `ControllerReturnScanner`, que lê o `return` dos métodos públicos de
# cada Controller.
#
# Fluxo exigido: Controller -> Resource -> Response.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import STRUCTURE, Rule, rule_code
from nucleus.rules.scanner.controller_return import ControllerReturn


class ControllerMustReturnResource(Rule):
    """
    Regra arquitetural:

    SOLAR-ROF-002

    Todo Controller deve retornar uma resposta que tenha passado por
    um Resource.

    Fluxo exigido:

        Controller → Resource → Response

    É VIOLAÇÃO:

        class UserController:

            @staticmethod
            def show():
                return {"id": 1, "name": "Ana"}, 200

    Correto:

        class UserController:

            @staticmethod
            def show():
                return UserResource.to_object(user), 200

    O que a regra procura é a CHAMADA ao Resource (`to_object` para
    um item, `collection` para uma lista): quem monta a representação
    da resposta é o Resource, e chamá-lo é o que tira do Controller a
    decisão do que sai.

    O motivo é o de sempre: sem o Resource, um campo interno
    (`password`, `secret_key`, um token) nasce exposto por descuido, e
    o cliente passa a depender dele. Quem decide o que é público é o
    Resource — e é a SOLAR-SEG-002 que julga o que ele expõe.

    Diferente das regras de dependência (SOLAR-RED-001 a SOLAR-RED-012), esta
    NÃO valida o grafo de imports. O contexto dela é o RETORNO de um
    método de Controller.
    """

    def code(self) -> str:
        return rule_code(STRUCTURE, 2)

    def description(self) -> str:
        return (
            "Todo Controller deve retornar uma resposta "
            "processada por um Resource."
        )

    def validate(self, controller_return: ControllerReturn) -> None:

        # Basta o retorno passar por um Resource: a regra não julga
        # QUAL nem o que ele expõe.
        if controller_return.uses_resource():
            return

        raise SolarException(
            self._build_message(controller_return)
        )

    def _build_message(
        self,
        controller_return: ControllerReturn
    ) -> str:

        return (
            f"{self.code()}: o Controller "
            f"'{controller_return.controller}."
            f"{controller_return.method}' retorna uma resposta que não "
            f"passa por um Resource. Toda resposta deve ser montada "
            f"por um Resource (ex.: "
            f"return UserResource.to_object(dado), 200)."
        )
