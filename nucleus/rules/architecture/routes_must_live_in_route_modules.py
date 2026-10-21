# SOLAR-ROF-004 — a rota mora em um `routes.py`.
#
# A ROF-004 tem DUAS verificações: o estilo da declaração (sem
# decorator) e o MÓDULO onde a rota mora. Esta classe cuida da
# segunda; a primeira é a RoutesMustBeDeclaredExplicitly.
# A ROF-005 diz para quem a rota aponta.
from pathlib import PurePosixPath

from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import STRUCTURE, Rule, rule_code
from nucleus.rules.scanner.route_declaration import RouteDeclaration


class RoutesMustLiveInRouteModules(Rule):
    """
    Regra arquitetural:

    SOLAR-ROF-004

    Toda rota HTTP deve ser declarada em um MÓDULO DE ROTAS próprio.

    Um módulo de rotas é identificado pelo caminho:

        orbits/routes.py             → composição central
        planets/<planet>/routes.py   → rotas do próprio Planet

    É PROIBIDO declarar rota em módulos que não sejam de rotas:

        planets/user/service.py
        planets/user/repository.py
        planets/user/usecases/create_user.py
        planets/user/controller.py
        planets/user/route.py            (nome não reconhecido)

    Exemplo válido:

        planets/auth/routes.py

            auth_routes.add_url_rule(
                "/login",
                "login",
                AuthController.login,
                methods=["POST"]
            )

    A regra complementa:

        SOLAR-ROF-004 → declarar sem decorator E em módulo de rotas;
        SOLAR-ROF-005 → apontar para Controller.

    O nome do arquivo de rotas é uma CONVENÇÃO DA SOLAR
    (ROUTE_MODULE_FILENAME), não um detalhe de framework.
    """

    # Nome do arquivo de rotas — o mesmo em todas as posições.
    ROUTE_MODULE_FILENAME = "routes.py"

    # Segmento que identifica a coleção de Planets
    # dentro do caminho de um módulo.
    PLANETS_SEGMENT = "planets"

    # Pacote central de composição de rotas em Orbits.
    ORBITS_PACKAGE = "orbits"

    def code(self) -> str:
        return rule_code(STRUCTURE, 4)

    def description(self) -> str:
        return (
            "Rotas devem ser declaradas em módulos de rotas "
            "próprios."
        )

    def validate(self, declaration: RouteDeclaration) -> None:

        # Pergunta única: o ARQUIVO onde a rota foi declarada é um
        # módulo de rotas? O estilo da declaração não importa aqui —
        # isso é assunto da outra verificação da SOLAR-ROF-004.
        if self._is_route_module(declaration.file):
            return

        raise SolarException(
            self._build_message(declaration)
        )

    def _is_route_module(self, file: str) -> bool:

        # `PurePosixPath` porque o caminho vem do scanner em formato
        # POSIX (barras normais), mesmo quando lido no Windows.
        parts = PurePosixPath(file).parts

        # Caminho vazio não deveria acontecer, mas `parts[-1]`
        # estouraria — e uma regra arquitetural não pode derrubar o
        # validador.
        if not parts:
            return False

        # Primeiro filtro: o nome do arquivo. Toda rota mora em um
        # `routes.py`; `route.py` (singular) NÃO conta.
        if parts[-1] != self.ROUTE_MODULE_FILENAME:
            return False

        # Segunda forma aceita: `planets/<planet>/routes.py`. O segmento
        # vale em qualquer profundidade, o que cobre os dois layouts
        # conhecidos.
        if self.PLANETS_SEGMENT in parts[:-1]:
            return True

        # Terceira forma: o ponto central `orbits/routes.py`, e SÓ ele —
        # `orbits/routes/` (pacote) e `orbits/x/routes.py` são
        # reprovados.
        return parts[:-1] == (self.ORBITS_PACKAGE,)

    def _build_message(
        self,
        declaration: RouteDeclaration
    ) -> str:

        return (
            f"{self.code()}: "
            f"a rota declarada em "
            f"{declaration.file}:{declaration.line} está fora de "
            f"um módulo de rotas. "
            f"Declare-a em 'planets/<planet>/"
            f"{self.ROUTE_MODULE_FILENAME}' ou no ponto central "
            f"'{self.ORBITS_PACKAGE}/{self.ROUTE_MODULE_FILENAME}'."
        )
