# Scanner do que cada Controller CONHECE diretamente.
#
# Um Controller deve orquestrar: receber, delegar ao UseCase e
# devolver um Resource. Quando ele importa `jwt`, `hashlib` ou
# `jose`, passou a FAZER segurança em vez de delegar — e é isso que
# este scanner descreve.
#
# Quais módulos são proibidos é política da SOLAR-SEG-003. Aqui só
# se lista o que foi importado.
import ast
from pathlib import Path

from nucleus.rules.scanner.controller_module import (
    is_controller_module
)
from nucleus.rules.scanner.controller_security_usage import (
    ControllerSecurityUsage
)
from nucleus.rules.scanner.source_files import source_files


class ControllerSecurityScanner:
    """
    Scanner responsável por identificar os Controllers e os
    módulos que cada um conhece diretamente.

    Um Controller é reconhecido por DOIS critérios: o arquivo tem
    que ser um MÓDULO de Controller (ver `controller_module`) e a
    classe tem que terminar em "Controller":

        planets/auth/controllers/auth_controller.py

            class AuthController:
                ...

    Para cada Controller, o scanner lista os módulos de topo
    importados no arquivo:

        import jwt            → "jwt"
        import hashlib        → "hashlib"
        from jose import jwt  → "jose"

    O scanner NÃO decide se um módulo é proibido: isso é
    responsabilidade da Rule SOLAR-SEG-003.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    CONTROLLER_SUFFIX = "Controller"

    def __init__(self, root: Path):
        self.root = root.resolve()

    def scan(self) -> list[ControllerSecurityUsage]:
        """
        Percorre o projeto e descreve cada Controller encontrado.
        """

        usages: list[ControllerSecurityUsage] = []

        for file in source_files(self.root):

            usages.extend(
                self._scan_file(file)
            )

        return usages

    def _scan_file(
        self,
        file: Path
    ) -> list[ControllerSecurityUsage]:
        """
        Analisa um único arquivo Python.
        """

        # Arquivo que não é de Controller não tem o que descrever. O
        # LUGAR decide — ver `controller_module`.
        if not is_controller_module(file):
            return []

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        relative = file.relative_to(self.root).as_posix()

        # Os imports são do ARQUIVO, não da classe, e por isso são
        # calculados UMA vez: todos os Controllers do mesmo arquivo
        # enxergam o mesmo conjunto. Isso é intencional — Python não
        # tem import por classe, e ignorar um import "de outro
        # Controller" do mesmo módulo seria fingir uma separação
        # que o código não tem.
        imports = frozenset(
            self._imports(tree)
        )

        usages: list[ControllerSecurityUsage] = []

        # Um Controller por classe. O arquivo já foi filtrado pelo
        # LUGAR; aqui o sufixo do nome separa as classes DENTRO dele.
        for node in ast.walk(tree):

            if not isinstance(node, ast.ClassDef):
                continue

            if not node.name.endswith(self.CONTROLLER_SUFFIX):
                continue

            usages.append(
                ControllerSecurityUsage(
                    controller=node.name,
                    imports=imports,
                    file=relative,
                    line=node.lineno
                )
            )

        return usages

    def _imports(self, tree: ast.AST) -> set[str]:
        """
        Coleta os módulos de TOPO importados no arquivo.
        """

        modules: set[str] = set()

        # Só o MÓDULO DE TOPO: `from jose.jwt import decode` conta
        # como "jose". É o topo que diz o que o Controller passou a
        # conhecer; o submódulo é detalhe.
        for node in ast.walk(tree):

            # `import a.b.c` — um `Import` pode trazer vários nomes
            # de uma vez.
            if isinstance(node, ast.Import):

                for alias in node.names:
                    modules.add(alias.name.split(".")[0])

            # `from a.b import c` — aqui o módulo é `node.module`.
            elif isinstance(node, ast.ImportFrom):

                # `node.module` é None no import relativo
                # (`from . import x`): não há topo para registrar.
                if node.module:
                    modules.add(node.module.split(".")[0])

        return modules
