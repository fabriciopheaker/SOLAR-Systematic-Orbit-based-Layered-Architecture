# Scanner das verificações de autenticação DENTRO do Controller.
#
# Dois vocabulários, porque são duas formas de verificar: o NOME
# (`current_user`, `has_permission`) e o CÓDIGO HTTP (`abort(401)`,
# `abort(403)`). Um Controller pode fazer só uma delas — as duas são
# descritas para a SOLAR-SEG-006 julgar.
import ast
from pathlib import Path

from nucleus.rules.scanner.controller_auth_checks import (
    ControllerAuthChecks
)
from nucleus.rules.scanner.controller_module import (
    is_controller_module
)
from nucleus.rules.scanner.source_files import source_files


class ControllerAuthCheckScanner:
    """
    Scanner responsável por identificar as VERIFICAÇÕES DE
    AUTENTICAÇÃO espalhadas pelo corpo de um Controller.

    Um Controller é reconhecido pelo LUGAR do arquivo — um módulo
    de Controller, ver `controller_module` — e pelo NOME da classe
    (terminado em "Controller"). No corpo da classe, o scanner
    procura:

        current_user              → "current_user"
        is_authenticated          → "is_authenticated"
        has_permission(...)       → "has_permission"
        verify_token(...)         → "verify_token"
        abort(401)                → "abort(401)"
        abort(403)                → "abort(403)"

    O scanner NÃO decide se há violação: isso é responsabilidade
    da Rule SOLAR-SEG-006.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    # Mesma convenção das outras regras de Controller: o arquivo é um
    # módulo de Controller e a classe traz o SUFIXO no nome.
    CONTROLLER_SUFFIX = "Controller"

    # Nomes que representam CONSULTA/VERIFICAÇÃO de autenticação.
    #
    # É uma lista por NOME, então vale a ressalva de sempre: um
    # identificador com esse nome que NÃO seja verificação de
    # autenticação (`has_role` de um domínio de RH, por exemplo) seria
    # marcado. É o limite conhecido da análise sem executar o código.
    AUTH_CHECKS = frozenset({
        "current_user",
        "is_authenticated",
        "login_required",
        "has_permission",
        "check_permission",
        "has_role",
        "check_role",
        "verify_token",
        "validate_token",
        "check_token",
    })

    # Códigos HTTP de autenticação/autorização.
    #
    # Só estes dois: `abort(404)` e `abort(400)` são erro de entrada ou
    # de rota, e não decisão sobre quem entra.
    AUTH_STATUS = frozenset({401, 403})

    def __init__(self, root: Path):
        self.root = root.resolve()

    def scan(self) -> list[ControllerAuthChecks]:
        """
        Percorre o projeto e descreve cada Controller encontrado.
        """

        findings: list[ControllerAuthChecks] = []

        for file in source_files(self.root):

            findings.extend(
                self._scan_file(file)
            )

        return findings

    def _scan_file(self, file: Path) -> list[ControllerAuthChecks]:
        """
        Analisa um único arquivo Python.
        """

        # Arquivo que não é de Controller não tem o que descrever.
        if not is_controller_module(file):
            return []

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        relative = file.relative_to(self.root).as_posix()

        findings: list[ControllerAuthChecks] = []

        # Um Controller por classe, pelo sufixo do nome, DENTRO de um
        # módulo de Controller — mesma convenção da SOLAR-SEG-003.
        for node in ast.walk(tree):

            if not isinstance(node, ast.ClassDef):
                continue

            if not node.name.endswith(self.CONTROLLER_SUFFIX):
                continue

            findings.append(
                ControllerAuthChecks(
                    controller=node.name,
                    # `frozenset`: o que importa é QUAIS verificações
                    # aparecem, não quantas vezes — repetir
                    # `current_user` três vezes é o mesmo problema.
                    checks=frozenset(
                        self._checks(node)
                    ),
                    file=relative,
                    line=node.lineno
                )
            )

        return findings

    def _checks(self, node: ast.ClassDef) -> set[str]:
        """
        Coleta as verificações de autenticação usadas no corpo da
        classe.
        """

        checks: set[str] = set()

        # `walk` na CLASSE: a verificação pode estar em qualquer método,
        # e é isso que caracteriza a DISPERSÃO que a regra persegue.
        for child in ast.walk(node):

            # Três formas de aparecer no código, e um identificador pode
            # cair em mais de uma: `current_user.is_authenticated` tem um
            # `Attribute` E um `Name`. Como o resultado é CONJUNTO, isso
            # não gera duplicata.
            if isinstance(child, ast.Attribute):

                if child.attr in self.AUTH_CHECKS:
                    checks.add(child.attr)

            elif isinstance(child, ast.Name):

                if child.id in self.AUTH_CHECKS:
                    checks.add(child.id)

            # Chamada é o caso do `abort(...)`, que não é nome nem
            # atributo de nada.
            elif isinstance(child, ast.Call):

                checks.update(
                    self._abort_check(child)
                )

        return checks

    def _abort_check(self, node: ast.Call) -> set[str]:
        """
        Identifica `abort(401)` / `abort(403)`.
        """

        func = node.func

        name = None

        # `abort` e `flask.abort` são a mesma função; o que muda é o nó
        # em que ela aparece.
        if isinstance(func, ast.Attribute):
            name = func.attr

        elif isinstance(func, ast.Name):
            name = func.id

        # `not node.args` cobre `abort()` sem argumento: não há status
        # para julgar.
        if name != "abort" or not node.args:
            return set()

        # Só o PRIMEIRO argumento, que é onde o status vai. Se não for
        # literal (`abort(code)` com variável), não dá para decidir
        # estaticamente — e o scanner prefere não acusar a acusar
        # errado.
        status = node.args[0]

        if not isinstance(status, ast.Constant):
            return set()

        if status.value in self.AUTH_STATUS:
            return {f"abort({status.value})"}

        return set()
