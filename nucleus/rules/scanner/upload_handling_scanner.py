# Scanner dos primitivos de ARQUIVO usados por um Controller.
#
# Coleta o que aparece no corpo da classe: chamada nativa (`open`,
# `copy`), módulo (`shutil`, `tempfile`) e nome solto. É a matéria-prima
# da SOLAR-ARCH-025.
import ast
from pathlib import Path

from nucleus.rules.scanner.controller_module import (
    is_controller_module
)
from nucleus.rules.scanner.source_files import source_files
from nucleus.rules.scanner.upload_handling import UploadHandling


class UploadHandlingScanner:
    """
    Scanner responsável por identificar os Controllers que
    manipulam ARQUIVO diretamente.

    Um Controller é reconhecido pelo LUGAR do arquivo — um módulo
    de Controller, ver `controller_module` — e pelo NOME da classe
    (terminado em "Controller"). No corpo da classe, o scanner
    procura PRIMITIVOS DE ARQUIVO:

        open(path, "wb")                     → "open"
        arquivo.write_bytes(conteudo)        → "write_bytes"
        arquivo.write_text(texto)            → "write_text"
        shutil.copy(origem, destino)         → "shutil"
        tempfile.NamedTemporaryFile()        → "tempfile"
        mimetypes.guess_type(nome)           → "mimetypes"

    O scanner NÃO decide se há violação: isso é responsabilidade
    da Rule SOLAR-ARCH-025.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    # Mesma convenção das outras regras de Controller: o arquivo é um
    # módulo de Controller e a classe traz o SUFIXO no nome.
    CONTROLLER_SUFFIX = "Controller"

    # Chamadas nativas que manipulam arquivo.
    #
    # Só os NOMES das funções, sem o módulo: o mesmo nome pode chegar
    # como `copy(...)` ou `shutil.copy(...)` — ver `_call_primitives`.
    FORBIDDEN_CALLS = frozenset({
        "open",
        "write_bytes",
        "write_text",
        "copy",
        "copy2",
        "copyfile",
        "move",
        "mkdtemp",
        "NamedTemporaryFile",
    })

    # Módulos de manipulação de arquivo.
    #
    # Listados à parte das chamadas porque às vezes o que aparece é só
    # o IMPORT (`import shutil`) — e importar já é sinal de que o
    # Controller vai mexer em arquivo.
    FILE_MODULES = frozenset({
        "shutil",
        "tempfile",
        "mimetypes",
        "aiofiles",
    })

    def __init__(self, root: Path):
        self.root = root.resolve()

    def scan(self) -> list[UploadHandling]:
        """
        Percorre o projeto e descreve cada Controller encontrado.
        """

        findings: list[UploadHandling] = []

        for file in source_files(self.root):

            findings.extend(
                self._scan_file(file)
            )

        return findings

    def _scan_file(self, file: Path) -> list[UploadHandling]:
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

        findings: list[UploadHandling] = []

        # Um Controller por classe, pelo sufixo do nome, DENTRO de um
        # módulo de Controller.
        for node in ast.walk(tree):

            if not isinstance(node, ast.ClassDef):
                continue

            if not node.name.endswith(self.CONTROLLER_SUFFIX):
                continue

            findings.append(
                UploadHandling(
                    controller=node.name,
                    # `frozenset`: o que importa é QUAIS primitivos
                    # aparecem, não quantas vezes — chamar `open` três
                    # vezes é o mesmo problema.
                    primitives=frozenset(
                        self._primitives(node)
                    ),
                    file=relative,
                    line=node.lineno
                )
            )

        return findings

    def _primitives(self, node: ast.ClassDef) -> set[str]:
        """
        Coleta os primitivos de arquivo usados no corpo da classe.
        """

        primitives: set[str] = set()

        # Três formas, porque a mesma coisa aparece de três jeitos no
        # código: `open(...)` é `Call`, `arquivo.write_bytes(...)` traz
        # `Attribute` e `shutil` solto é `Name`.
        for child in ast.walk(node):

            if isinstance(child, ast.Call):
                primitives.update(
                    self._call_primitives(child)
                )

            elif isinstance(child, ast.Attribute):

                if child.attr in self.FILE_MODULES:
                    primitives.add(child.attr)

            elif isinstance(child, ast.Name):

                if child.id in self.FILE_MODULES:
                    primitives.add(child.id)

        return primitives

    def _call_primitives(self, node: ast.Call) -> set[str]:
        """
        Identifica chamadas de manipulação de arquivo.
        """

        func = node.func

        # `open(...)` — função nativa chamada direto.
        if isinstance(func, ast.Name):

            if func.id in self.FORBIDDEN_CALLS:
                return {func.id}

            return set()

        # `arquivo.write_bytes(...)` e `shutil.copy(...)` — nos dois o
        # nome da função vem DEPOIS do ponto, e é ele que compara com a
        # lista.
        if isinstance(func, ast.Attribute):

            if func.attr in self.FORBIDDEN_CALLS:
                return {func.attr}

            return set()

        # Chamada sobre outra chamada (`x().y()`) ou sobre subscrito:
        # nada a registrar.
        return set()
