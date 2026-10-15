# O vocabulário de ROTAS de um framework.
#
# Existe para a regra de roteamento não citar Flask: a Rule pergunta
# "este nome é um decorator de rota?", e quem responde é a convenção
# injetada. Trocar de framework vira trocar a convenção.
import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingConvention:
    """
    Descreve COMO um framework declara rotas.

    A SOLAR não deve ficar presa a um framework específico.
    Cada framework fornece sua própria RoutingConvention, e o
    RouteScanner usa a convenção para reconhecer as declarações.

    route_decorators:
        Nomes de decorators que declaram rotas
        (ex.: "route" para @app.route).

    route_registrations:
        Nomes de funções que registram rotas explicitamente
        (ex.: "add_url_rule").

    Dessa forma, adicionar suporte a outro framework não exige
    alterar a Rule: basta fornecer outra RoutingConvention.
    """

    name: str

    # Dois vocabulários porque há DUAS formas de declarar rota: o
    # decorator (`@bp.route`) e o registro por chamada
    # (`bp.add_url_rule`). A SOLAR-ARCH-019 aceita qualquer uma
    # delas.
    route_decorators: frozenset[str]
    route_registrations: frozenset[str]


def is_super_delegation(node: ast.Call) -> bool:
    """
    Indica se a chamada é `super().algo(...)`.

    É a chamada da BASE — quem ESTENDE o framework delegando a ele —, e
    não a declaração de uma rota no código da aplicação:

        class SolarBlueprint(Blueprint):
            def add_url_rule(self, ...):
                ...
                super().add_url_rule(...)   ← delegação, não rota

    Sem esta distinção, o mecanismo que existe para deixar a ROTA
    declarar os guardas seria acusado pelas regras de rota — que é
    exatamente o contrário do que ele serve.
    """

    if not isinstance(node.func, ast.Attribute):
        return False

    value = node.func.value

    if not isinstance(value, ast.Call):
        return False

    return (
        isinstance(value.func, ast.Name)
        and value.func.id == "super"
    )


def flask_routing_convention() -> RoutingConvention:
    """
    Convenção de roteamento do Flask.

    Decorators:
        @app.route(...)
        @blueprint.route(...)
        @api.route(...)
        @router.get(...) / @router.post(...) / etc.

    Registro explícito:
        blueprint.add_url_rule(...)
    """

    # `get`/`post`/... entram junto de `route` porque um `MethodView`
    # ou um Router de extensão declara rota pelo VERBO
    # (`@router.get("/x")`) — e isso é declaração de rota, mesmo sem
    # a palavra "route" no código.
    return RoutingConvention(
        name="flask",
        route_decorators=frozenset({
            "route",
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
        }),
        # O registro explícito é o caso de `routes.py`, onde a rota
        # é montada por chamada e não por decorator.
        route_registrations=frozenset({
            "add_url_rule",
        }),
    )
