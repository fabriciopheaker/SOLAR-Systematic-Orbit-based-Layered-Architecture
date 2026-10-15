# Scanner dos CAMPOS que um Resource expõe.
#
# O que ele descreve é o DICIONÁRIO que o Resource monta — as
# chaves de texto usadas no corpo da classe. É por ali que um campo
# sensível escapa: o Resource é a última etapa antes de a resposta
# sair.
#
# Descrição, não julgamento: quais campos não podem sair é política
# da SOLAR-ARCH-021.
import ast
from pathlib import Path

from nucleus.rules.scanner.resource_exposure import ResourceExposure
from nucleus.rules.scanner.source_files import source_files


class ResourceExposureScanner:
    """
    Scanner responsável por identificar os CAMPOS EXPOSTOS por um
    Resource.

    Um Resource é reconhecido pelo NOME da classe (terminado em
    "Resource") ou por declarar `Resource` como base:

        class UserResource(Resource):
            ...

    Os campos expostos são as CHAVES de texto usadas no corpo da
    classe:

            return {
                "id": data["id"],
                "password": data["password"],    ← exposto
            }

    O scanner NÃO decide se há violação: isso é responsabilidade
    da Rule SOLAR-ARCH-021.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    # Reconhecer pelo SUFIXO do nome é convenção do projeto, e não
    # uma checagem de herança real. A escolha é deliberada: pega
    # também o Resource que nem importa a base — que está mais
    # errado ainda.
    RESOURCE_SUFFIX = "Resource"

    def __init__(self, root: Path):
        self.root = root.resolve()

    def scan(self) -> list[ResourceExposure]:
        """
        Percorre o projeto e descreve cada Resource encontrado.
        """

        resources: list[ResourceExposure] = []

        for file in source_files(self.root):

            resources.extend(
                self._scan_file(file)
            )

        return resources

    def _scan_file(self, file: Path) -> list[ResourceExposure]:
        """
        Analisa um único arquivo Python.
        """

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        relative = file.relative_to(self.root).as_posix()

        resources: list[ResourceExposure] = []

        for node in ast.walk(tree):

            if not isinstance(node, ast.ClassDef):
                continue

            if not self._is_resource(node):
                continue

            resources.append(
                ResourceExposure(
                    resource=node.name,
                    # `frozenset`: duas leituras do mesmo Resource
                    # têm que dar o mesmo resultado independente da
                    # ordem em que as chaves aparecem no código.
                    fields=frozenset(
                        self._fields(node)
                    ),
                    file=relative,
                    line=node.lineno
                )
            )

        return resources

    def _is_resource(self, node: ast.ClassDef) -> bool:
        """
        Classifica uma classe como Resource pelo nome ou pela base.
        """

        if node.name.endswith(self.RESOURCE_SUFFIX):
            return True

        # Ou herda de algo cujo nome termina em "Resource".
        # `_name` reduz a expressão ao nome FINAL
        # (`nucleus.Resource` → "Resource"), porque é só ele que
        # interessa para o sufixo.
        return any(
            self._name(base).endswith(self.RESOURCE_SUFFIX)
            for base in node.bases
        )

    def _fields(self, node: ast.ClassDef) -> set[str]:
        """
        Coleta as chaves de texto dos dicionários do corpo da
        classe — são elas que representam o que o Resource expõe.
        """

        fields: set[str] = set()

        # `walk` na CLASSE, não no arquivo: o campo exposto é o que
        # aparece dentro da classe, em qualquer método — inclusive
        # num `render` que delega para um auxiliar.
        for child in ast.walk(node):

            if not isinstance(child, ast.Dict):
                continue

            for key in child.keys:

                if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                ):
                    fields.add(key.value)

        return fields

    def _name(self, node: ast.AST) -> str:
        """
        Extrai o nome final de uma expressão.

            Resource            → "Resource"
            nucleus.Resource    → "Resource"
        """

        # `nucleus.Resource` chega como Attribute; `Resource`
        # sozinho chega como Name. Em ambos o que importa é o nome
        # final — a origem do import não muda o sufixo.
        if isinstance(node, ast.Attribute):
            return node.attr

        if isinstance(node, ast.Name):
            return node.id

        # Expressão que não é nome nem atributo (ex.: chamada):
        # string vazia, que não termina com o sufixo.
        return ""
