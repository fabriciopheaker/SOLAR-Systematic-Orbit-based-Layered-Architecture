# SOLAR-ROF-005 — a rota tem que desembocar em um Controller.
#
# É o par da SOLAR-ROF-004: ela cuida de COMO e ONDE a rota é
# declarada; esta cuida de PARA QUEM ela aponta. Juntas, garantem que o fluxo
# Orbit -> Planet Routes -> Controller exista de verdade.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import STRUCTURE, Rule, rule_code
from nucleus.rules.scanner.route_declaration import RouteDeclaration


class RoutesMustPointToController(Rule):
    """
    Regra arquitetural:

    SOLAR-ROF-005

    Toda rota deve apontar para um Controller.

    Fluxo exigido:

        Orbits → Planet Routes → Controller → Input → UseCase
        → Entity / Repository → Output → Resource → HTTP Response

    É PROIBIDO uma rota apontar diretamente para:

        - UseCase
        - Repository
        - Entity
        - Service
        - qualquer componente de domínio ou persistência
        - lambda / expressão inline

    Exemplo proibido:

        api.add_url_rule("/users", "create", CreateUserUseCase.execute)
        api.add_url_rule("/api", "home", lambda: jsonify({...}))

    Exemplo correto:

        api.add_url_rule("/users", "create", UserController.create)

    ESCOPO: esta regra avalia apenas rotas registradas
    explicitamente (REGISTRATION). Rotas declaradas por decorator
    são tratadas pela SOLAR-ROF-004.
    """

    # Sufixo que identifica um Controller da SOLAR.
    #
    # Mesma convenção da SOLAR-SEG-003: o reconhecimento é pelo
    # NOME. É o que o scanner consegue ver sem executar o código —
    # descobrir a classe de verdade exigiria importar a aplicação.
    CONTROLLER_SUFFIX = "Controller"

    def code(self) -> str:
        return rule_code(STRUCTURE, 5)

    def description(self) -> str:
        return "Toda rota deve apontar para um Controller."

    def validate(self, declaration: RouteDeclaration) -> None:

        # Só o estilo REGISTRATION: a rota por decorator nem chega a
        # ser avaliada aqui — ela já é violação da SOLAR-ROF-004, e
        # apontar o mesmo trecho duas vezes só faria ruído.
        if declaration.style != RouteDeclaration.REGISTRATION:
            return

        if self._points_to_controller(declaration):
            return

        raise SolarException(
            self._build_message(declaration)
        )

    def _points_to_controller(
        self,
        declaration: RouteDeclaration
    ) -> bool:

        owner = self._controller_owner(declaration.target)

        if owner is None:
            return False

        return owner.endswith(self.CONTROLLER_SUFFIX)

    def _controller_owner(self, target: str | None) -> str | None:
        """
        Extrai o "dono" de um alvo de rota.

            "AuthController.login"     → "AuthController"
            "AuthController().login"   → "AuthController"

        Retorna None quando o alvo não é uma referência
        qualificada (ex.: lambda ou expressão inline).
        """

        # `not target` cobre `None` e `""`: lambda e expressão inline
        # chegam sem alvo — não são referência qualificada.
        if not target:
            return None

        # `replace("()", "")` normaliza `AuthController().login`
        # para `AuthController.login`, para os dois casos terem a
        # mesma leitura.
        parts = target.replace("()", "").split(".")

        # Menos de dois segmentos = nome solto (`login`), sem dono.
        if len(parts) < 2:
            return None

        # `[-2]` e não `[-1]`: o último segmento é o MÉTODO
        # (`login`); o dono é o penúltimo (`AuthController`).
        return parts[-2]

    def _build_message(
        self,
        declaration: RouteDeclaration
    ) -> str:

        target = declaration.target or "<sem alvo>"

        return (
            f"{self.code()}: "
            f"a rota registrada em "
            f"{declaration.file}:{declaration.line} "
            f"('{declaration.mechanism}') aponta para '{target}', "
            f"que não é um Controller. "
            f"Toda rota deve apontar para um Controller "
            f"(ex.: UserController.create)."
        )
