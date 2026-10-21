# Scanner de CLASSES POR ARQUIVO.
#
# É o único scanner que pode não devolver nada para um arquivo: arquivo
# sem classe não gera contexto (ver `_scan_file`). Isso mantém o
# contexto alinhado com a pergunta da SOLAR-ROF-007 — "este arquivo
# declara mais de um Model?" — que não faz sentido para arquivo sem
# classe.
import ast
from pathlib import Path

from nucleus.rules.scanner.module_classes import (
    DeclaredClass,
    ModuleClasses,
)
from nucleus.rules.scanner.source_files import (
    resolve_exclusions,
    source_files,
)


class ModuleClassesScanner:
    """
    Scanner responsável por descrever as CLASSES declaradas em cada
    arquivo do projeto.

    Responde:

        "Quais classes este arquivo declara, e em que linha?"

    O scanner NÃO decide quantas são demais: isso é
    responsabilidade da Rule SOLAR-ROF-007.

    Ele descreve TODO arquivo que declara ao menos uma classe —
    inclusive os que têm uma só, e inclusive classes que não são
    Model. Assim o mesmo scanner serve a qualquer regra que fale
    sobre classes por arquivo.

    Diretórios técnicos (cache, ambiente virtual, build) e
    diretórios de teste ficam de fora — ver
    nucleus.rules.scanner.source_files.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    # Nome do módulo que marca um PACOTE: `__init__.py` não é um módulo
    # a mais, é o próprio diretório.
    PACKAGE_INIT = "__init__"

    def __init__(
        self,
        root: Path,
        excluded_directories=None
    ):
        self.root = root.resolve()

        # `resolve_exclusions` completa a lista com o padrão; passar uma
        # coleção VAZIA desliga a exclusão (é como um teste exercita um
        # arquivo dentro de `tests/`).
        self.excluded_directories = resolve_exclusions(
            excluded_directories
        )

    def scan(self) -> list[ModuleClasses]:
        """
        Percorre o projeto e descreve os arquivos com classes.
        """

        modules: list[ModuleClasses] = []

        for file in source_files(
            self.root,
            self.excluded_directories
        ):

            # `None` = arquivo sem classe. Só entra no resultado quem
            # tem o que descrever.
            module = self._scan_file(file)

            if module is not None:
                modules.append(module)

        return modules

    def _scan_file(self, file: Path) -> ModuleClasses | None:
        """
        Descreve as classes de um arquivo.

        Devolve None quando o arquivo não declara classe alguma.
        """

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        # Ordem de LINHA, não de percurso da AST: classes aninhadas
        # apareceriam fora de ordem com ast.walk.
        declared = sorted(
            (
                DeclaredClass(name=node.name, line=node.lineno)
                for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
            ),
            key=lambda item: item.line
        )

        # Arquivo sem classe não vira contexto: não há pergunta a
        # responder sobre ele.
        if not declared:
            return None

        # `as_posix()`: o relatório tem que sair igual no Windows e no
        # contêiner.
        relative = file.relative_to(self.root).as_posix()

        return ModuleClasses(
            module=self._module_name(file),
            file=relative,
            classes=tuple(declared)
        )

    def _module_name(self, file: Path) -> str:
        """
        Caminho pontuado do módulo.

            orbits/database/models/user_model.py   →
                "orbits.database.models.user_model"

            orbits/database/models/__init__.py     →
                "orbits.database.models"
        """

        # `list(...)` porque abaixo a lista é MODIFICADA — `parts` de um
        # `Path` é tupla.
        parts = list(
            file.relative_to(self.root).with_suffix("").parts
        )

        # `parts and` antes do `[-1]`: caminho vazio estouraria a
        # indexação.
        #
        # `__init__` é o marcador do pacote: o módulo é o próprio
        # pacote.
        if parts and parts[-1] == self.PACKAGE_INIT:
            parts.pop()

        return ".".join(parts)

