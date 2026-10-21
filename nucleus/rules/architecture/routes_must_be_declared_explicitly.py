# SOLAR-ROF-004 — rota por DECORATOR é proibida.
#
# Esta regra não conhece Flask: ela pergunta o ESTILO da declaração
# (`RouteDeclaration`), e quem sabe o que é um decorator de rota é a
# `RoutingConvention` injetada no scanner. Trocar de framework não
# muda uma linha aqui.
#
# O ALVO da rota (tem que ser um Controller) é a SOLAR-ROF-005.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import STRUCTURE, Rule, rule_code
from nucleus.rules.scanner.route_declaration import RouteDeclaration


class RoutesMustBeDeclaredExplicitly(Rule):
    """
    Regra arquitetural:

    SOLAR-ROF-004

    Toda rota HTTP deve ser declarada de forma EXPLÍCITA, em um
    módulo próprio de rotas.

    É PROIBIDO declarar rotas através de decorators do framework:

        @app.route(...)
        @blueprint.route(...)
        @api.route(...)
        @router.get(...) / @router.post(...) / etc.

    A declaração deve utilizar o mecanismo explícito de registro
    fornecido pelo framework. No Flask:

        auth_routes = Blueprint("auth", __name__)

        auth_routes.add_url_rule(
            "/login",
            "login",
            AuthController.login,
            methods=["POST"]
        )

    A detecção é guiada pela RoutingConvention do framework, e o
    scanner produz RouteDeclarations. Esta Rule não conhece Flask:
    ela decide com base na convenção utilizada pelo scanner.

    O ALVO da rota (deve ser um Controller) é responsabilidade
    da SOLAR-ROF-005.

    ESCOPO — o que esta regra NÃO cobre:

    Estruturas de dados (listas, dicts, objetos) usadas dentro de
    um módulo de rotas NÃO são violação. A regra observa apenas
    COMO a rota é declarada.
    """

    def code(self) -> str:
        return rule_code(STRUCTURE, 4)

    def description(self) -> str:
        return (
            "Rotas devem ser declaradas explicitamente em módulos "
            "de rotas, sem decorators de framework."
        )

    def validate(self, declaration: RouteDeclaration) -> None:

        # Só o estilo DECORATOR é acusado; o estilo explícito passa.
        # A comparação é pelo que o SCANNER concluiu — e não por uma
        # busca de "@" no texto — porque só a AST diz com certeza
        # que aquilo é um decorator sendo aplicado.
        if declaration.style != RouteDeclaration.DECORATOR:
            return

        raise SolarException(
            self._build_message(declaration)
        )

    def _build_message(
        self,
        declaration: RouteDeclaration
    ) -> str:

        return (
            f"{self.code()}: "
            f"a rota '{declaration.target}' foi declarada por "
            f"decorator '@{declaration.mechanism}' em "
            f"{declaration.file}:{declaration.line}. "
            f"Rotas devem ser registradas explicitamente em um "
            f"módulo de rotas (ex.: Blueprint + add_url_rule)."
        )
