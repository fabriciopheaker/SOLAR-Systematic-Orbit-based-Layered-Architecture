# Scanner de DECLARAÇÃO DE ROTA.
#
# Responde "quem declara rota, e como?" — diferente do
# `ArchitectureScanner`, que responde "quem depende de quem". São as
# duas perguntas que as regras fazem sobre o código.
#
# A detecção é guiada por uma `RoutingConvention` injetada: este
# arquivo não cita Flask em nenhum ponto. Trocar de framework é passar
# outra convenção.
import ast
from pathlib import Path

from nucleus.rules.scanner.route_declaration import RouteDeclaration
from nucleus.rules.scanner.routing_convention import (
    RoutingConvention,
    flask_routing_convention,
    is_super_delegation,
)
from nucleus.rules.scanner.source_files import source_files


class RouteScanner:
    """
    Scanner responsável por identificar DECLARAÇÕES DE ROTA
    no código-fonte.

    Diferente do ArchitectureScanner — que responde
    "quem depende de quem" — este scanner responde:

        "Quem declara rotas, e como?"

    O scanner NÃO decide se uma declaração é permitida.
    A validação é responsabilidade do RuleEngine e das Rules.

    A detecção é guiada por uma RoutingConvention, o que mantém
    o scanner desacoplado do framework (Flask, hoje).

    Exemplo:

        planets/auth/routes.py

            auth_routes.add_url_rule(
                "/login",
                "login",
                AuthController.login,
                methods=["POST"]
            )

    O scanner produzirá:

        module    = "planets.auth.routes"
        style     = "registration"
        mechanism = "add_url_rule"
        target    = "AuthController.login"
    """

    def __init__(
        self,
        root: Path,
        convention: RoutingConvention | None = None
    ):
        """
        Inicializa o Scanner.

        Args:
            root:
                Diretório raiz do projeto analisado.

            convention:
                Convenção de roteamento do framework.
                Por padrão, utiliza a convenção do Flask.
        """

        self.root = root.resolve()

        # Injetável, com o Flask como PADRÃO: o teste passa uma
        # convenção própria para provar que o scanner não conhece o
        # framework.
        self.convention = (
            convention or flask_routing_convention()
        )

    def scan(self) -> list[RouteDeclaration]:
        """
        Analisa todo o projeto e retorna as declarações de rota
        encontradas.
        """

        declarations: list[RouteDeclaration] = []

        for file in source_files(self.root):

            declarations.extend(
                self._scan_file(file)
            )

        return declarations

    def _scan_file(
        self,
        file: Path
    ) -> list[RouteDeclaration]:
        """
        Analisa um único arquivo Python.

        O código NÃO é executado: a análise é feita sobre a AST.
        """

        source_code = file.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(
            source_code,
            filename=str(file)
        )

        module = self._module_name(file)
        relative = self._relative_file(file)

        declarations: list[RouteDeclaration] = []

        # Duas formas de declarar rota, e cada uma mora em um nó
        # diferente: o decorator fica grudado na FUNÇÃO, e o registro
        # explícito é uma CHAMADA. Daí os dois `isinstance`.
        #
        # `AsyncFunctionDef` entra junto porque `async def` também pode
        # ser decorado — é o caso das views assíncronas.
        for node in ast.walk(tree):

            # Rotas declaradas por decorator do framework.
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef)
            ):

                declarations.extend(
                    self._decorator_declarations(
                        node,
                        module,
                        relative
                    )
                )

            # Rotas registradas explicitamente.
            elif isinstance(node, ast.Call):

                declaration = self._registration_declaration(
                    node,
                    module,
                    relative
                )

                if declaration is not None:
                    declarations.append(declaration)

        return declarations

    def _decorator_declarations(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        module: str,
        relative: str
    ) -> list[RouteDeclaration]:
        """
        Identifica decorators de roteamento em uma função.
        """

        declarations: list[RouteDeclaration] = []

        # `decorator_list` traz os decorators na ordem em que foram
        # escritos. Quem decide o que é rota é a CONVENÇÃO.
        for decorator in node.decorator_list:

            name = self._callable_name(decorator)

            # `not in` e não `==`: a convenção tem um CONJUNTO de nomes
            # aceitos (`route`, `get`, `post`, ...).
            if name not in self.convention.route_decorators:
                continue

            # `line=decorator.lineno` e não `node.lineno`: a linha do
            # problema é a do `@app.route`, não a do `def`.
            #
            # `target=node.name`: o alvo de um decorator é a própria
            # função decorada, e o nome dela é o que a SOLAR-ROF-005
            # vai julgar.
            declarations.append(
                RouteDeclaration(
                    module=module,
                    file=relative,
                    line=decorator.lineno,
                    style=RouteDeclaration.DECORATOR,
                    mechanism=name,
                    target=node.name
                )
            )

        return declarations

    def _registration_declaration(
        self,
        node: ast.Call,
        module: str,
        relative: str
    ) -> RouteDeclaration | None:
        """
        Identifica o registro explícito de uma rota.

        Exemplo:

            blueprint.add_url_rule(
                "/login",
                "login",
                AuthController.login,
                methods=["POST"]
            )

        Operações que NÃO declaram rota — como
        `api.register_blueprint(auth_routes)` — não produzem
        declaração: elas compõem módulos de rota, não rotas.
        """

        # `super().add_url_rule(...)` é a DELEGAÇÃO de um mecanismo que
        # estende o framework — o `SolarBlueprint`, por exemplo —, e não
        # a declaração de uma rota. A rota que quem USA o mecanismo
        # declara é lida onde ela foi escrita.
        if is_super_delegation(node):
            return None

        name = self._callable_name(node.func)

        # `func` é o que está sendo CHAMADO (`bp.add_url_rule`), e é o
        # nome dele que a convenção reconhece. `register_blueprint` não
        # está na lista — ele compõe módulos de rota, não declara rota.
        if name not in self.convention.route_registrations:
            return None

        return RouteDeclaration(
            module=module,
            file=relative,
            line=node.lineno,
            style=RouteDeclaration.REGISTRATION,
            mechanism=name,
            target=self._view_function(node)
        )

    def _view_function(self, node: ast.Call) -> str | None:
        """
        Extrai o alvo (view function) de um registro de rota.

        Aceita tanto `view_func=` quanto a posição utilizada
        pelo Flask:
            add_url_rule(rule, endpoint, view_func, ...)
        """

        # Primeiro a forma NOMEADA (`view_func=`), que é mais legível e
        # não depende da ordem dos argumentos.
        for keyword in node.keywords:

            if keyword.arg == "view_func":
                return self._expression(keyword.value)

        # Depois a forma POSICIONAL, que é a do Flask:
        # `add_url_rule(rule, endpoint, view_func, ...)` — o alvo é o
        # TERCEIRO argumento, índice 2.
        if len(node.args) >= 3:
            return self._expression(node.args[2])

        return None

    def _expression(self, node: ast.AST) -> str:
        """
        Converte uma expressão da AST em texto.

        Lambdas e expressões inline são marcadas para que a Rule
        perceba que a rota não aponta para um Controller.
        """

        # Lambda ganha um marcador legível: `ast.unparse` de uma lambda
        # devolveria o código dela inteiro, e o que a SOLAR-ROF-005
        # precisa saber é que ali NÃO há um Controller.
        if isinstance(node, ast.Lambda):
            return "<lambda>"

        # `ast.unparse` reconstrói a expressão como texto
        # (`AuthController.login`) sem precisar avaliá-la.
        return ast.unparse(node)

    def _callable_name(self, node: ast.AST) -> str | None:
        """
        Retorna o nome de um chamável/decorator.

            @app.route(...)      → "route"
            @router.get(...)     → "get"
            api.add_url_rule(...) → "add_url_rule"
            @route(...)          → "route"
        """

        # Aceita tanto o decorator já aplicado (`@app.route(...)`, que
        # chega como `Call`) quanto o nome solto.
        if isinstance(node, ast.Call):
            node = node.func

        # `app.route` → o que interessa é o ÚLTIMO nome (`route`); o
        # objeto (`app`) não entra na decisão, porque a convenção olha
        # só o vocabulário.
        if isinstance(node, ast.Attribute):
            return node.attr

        # `@route(...)` sem objeto na frente chega como `Name`.
        if isinstance(node, ast.Name):
            return node.id

        return None

    def _module_name(self, file: Path) -> str:
        """
        Converte o caminho do arquivo em nome de módulo.

        planets/auth/routes.py → "planets.auth.routes"
        """

        relative = file.relative_to(self.root)

        # `with_suffix("")` tira o `.py`; as partes viram o caminho
        # pontuado. Conversão de formato, sem import envolvido.
        return ".".join(
            relative.with_suffix("").parts
        )

    def _relative_file(self, file: Path) -> str:
        """
        Retorna o caminho do arquivo relativo à raiz do projeto.
        """

        # `as_posix()` para o caminho sair com barras normais mesmo
        # lido no Windows: o relatório precisa ser igual nos dois
        # ambientes, e a SOLAR-ROF-004 compara partes do caminho.
        return file.relative_to(self.root).as_posix()
