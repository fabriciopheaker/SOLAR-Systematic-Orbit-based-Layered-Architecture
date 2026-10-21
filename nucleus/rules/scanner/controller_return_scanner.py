# Scanner do RETORNO dos métodos de Controller.
#
# Responde "o que cada Controller devolve?" — o fato que a
# SOLAR-ROF-002 lê. A análise é feita sobre a AST: o código NÃO é
# executado.
#
# O critério de "isto é um Controller" é o LUGAR da peça (um módulo
# de `controllers/`, ou um `controller.py`), e não só o sufixo do
# nome da classe — ver `controller_module`.
import ast
from pathlib import Path

from nucleus.rules.scanner.controller_module import (
    is_controller_module
)
from nucleus.rules.scanner.controller_return import ControllerReturn
from nucleus.rules.scanner.source_files import source_files


class ControllerReturnScanner:
    """
    Scanner responsável por descrever o retorno dos Controllers.

    Diferente do `ControllerSecurityScanner` — que responde "quais
    módulos um Controller conhece" — este responde:

        "O que cada Controller devolve?"

    O scanner NÃO decide se o retorno é válido: isso é
    responsabilidade da Rule SOLAR-ROF-002.

    Exemplo:

        planets/example/controllers/create_user_controller.py

            class CreateUserController:

                @staticmethod
                def create() -> tuple[dict, int]:
                    ...
                    return UserResource.to_object(output), 201

    O scanner produzirá:

        controller = "CreateUserController"
        method     = "create"
        resources  = {"UserResource"}
    """

    # Convenção de nome que identifica um Controller.
    CONTROLLER_SUFFIX = "Controller"

    # Os métodos que MONTAM a representação da resposta. São as
    # chamadas que a SOLAR-ROF-002 procura no retorno: `to_object`
    # para um item, `collection` para uma lista.
    RESOURCE_METHODS = ("to_object", "collection")

    # Métodos com este prefixo não respondem requisição: `__init__` e
    # os auxiliares internos. Fora daqui, senão um helper privado
    # acusaria uma violação que não existe.
    PRIVATE_PREFIX = "_"

    def __init__(self, root: Path):
        self.root = root.resolve()

    def scan(self) -> list[ControllerReturn]:
        """
        Percorre o projeto e descreve o retorno de cada Controller.
        """

        returns: list[ControllerReturn] = []

        for file in source_files(self.root):

            returns.extend(
                self._scan_file(file)
            )

        return returns

    def _scan_file(
        self,
        file: Path
    ) -> list[ControllerReturn]:
        """
        Analisa um único arquivo Python.
        """

        # Arquivo que não é de Controller não tem o que descrever — e
        # é aqui que o sufixo do nome da CLASSE deixa de ser o único
        # critério.
        if not is_controller_module(file):
            return []

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        relative = file.relative_to(self.root).as_posix()

        returns: list[ControllerReturn] = []

        for node in ast.walk(tree):

            if not isinstance(node, ast.ClassDef):
                continue

            if not node.name.endswith(self.CONTROLLER_SUFFIX):
                continue

            for method in node.body:

                if not isinstance(
                    method,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    continue

                if method.name.startswith(self.PRIVATE_PREFIX):
                    continue

                # UM alvo por MÉTODO: dois métodos de Controller são
                # duas respostas diferentes, e a regra precisa poder
                # julgar cada uma.
                returns.append(
                    ControllerReturn(
                        controller=node.name,
                        method=method.name,
                        resources=frozenset(
                            self._resource_names(method)
                        ),
                        file=relative,
                        line=method.lineno
                    )
                )

        return returns

    def _resource_names(self, method: ast.AST) -> list[str]:
        """
        Os nomes em que o Resource foi chamado, em qualquer `return`.

            return UserResource.to_object(output), 201
                → "UserResource"

            return resource.to_object(output), 200
                → "resource"

            return UserResource.collection(users), 200
                → "UserResource"

        O que importa é a CHAMADA: é ela que faz a representação da
        resposta passar pelo Resource.
        """

        names: list[str] = []

        for node in ast.walk(method):

            if not isinstance(node, ast.Return):
                continue

            names.extend(
                self._resource_calls(node)
            )

        return names

    def _resource_calls(self, node: ast.AST) -> list[str]:
        """
        As chamadas a método de Resource dentro de uma expressão de
        retorno.
        """

        calls: list[str] = []

        for child in ast.walk(node):

            if not isinstance(child, ast.Call):
                continue

            # Só `algo.to_object(...)`: uma chamada solta
            # (`to_object(x)`) não diz em QUEM o nome foi chamado, e
            # a regra precisa do nome do Resource para a mensagem.
            if not isinstance(child.func, ast.Attribute):
                continue

            if child.func.attr not in self.RESOURCE_METHODS:
                continue

            calls.append(
                ast.unparse(child.func.value)
            )

        return calls
