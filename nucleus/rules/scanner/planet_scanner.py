# Scanner de Planet: quais existem e o que há na raiz de cada um.
#
# Este NÃO usa `source_files`: ali o que interessa são ARQUIVOS de
# código, e aqui são DIRETÓRIOS. O que ele reusa daquele módulo é só a
# decisão de "isto está excluído?", para um Planet de fixture não contar
# como Planet.
from pathlib import Path

from nucleus.rules.scanner.planet_structure import PlanetStructure
from nucleus.rules.scanner.source_files import (
    is_inside_excluded,
    resolve_exclusions,
)


class PlanetScanner:
    """
    Scanner responsável por identificar os Planets da aplicação
    e descrever a estrutura da raiz de cada um.

    Um Planet é um diretório posicionado imediatamente abaixo de
    um segmento "planets":

        planets/user/
        orbits/planets/user/

    O scanner responde apenas:

        "Quais são os Planets e o que existe na raiz de cada um?"

    A validação das regras arquiteturais é responsabilidade do
    RuleEngine e das Rules.
    """

    # Segmento que identifica a coleção de Planets
    # dentro do caminho de um diretório.
    PLANETS_SEGMENT = "planets"

    # Diretórios que nunca descrevem a estrutura do Planet.
    #
    # Só `__pycache__`: ele nasce de uma execução e apareceria como
    # "peça extra" de todo Planet. Os outros nomes técnicos já foram
    # barrados antes, por `is_inside_excluded`.
    IGNORED_DIRECTORIES = frozenset({
        "__pycache__",
    })

    def __init__(self, root: Path):
        """
        Inicializa o Scanner.

        Args:
            root:
                Diretório raiz do projeto analisado.
        """

        self.root = root.resolve()

    def scan(self) -> list[PlanetStructure]:
        """
        Percorre o projeto e descreve cada Planet encontrado.
        """

        planets: list[PlanetStructure] = []

        # `rglob("*")` traz arquivos E diretórios — só os diretórios
        # interessam, porque o que se descreve é a RAIZ do Planet.
        # `sorted` para a ordem ser estável entre execuções.
        for path in sorted(self.root.rglob("*")):

            if not path.is_dir():
                continue

            # Teste e diretório técnico não descrevem a arquitetura:
            # um Planet de fixture não é um Planet.
            if is_inside_excluded(path, self.root):
                continue

            # `is_inside_excluded` olha só os diretórios ACIMA do
            # caminho. O PRÓPRIO candidato precisa ser checado aqui —
            # sem isso, `orbits/planets/__pycache__` seria lido como
            # um Planet.
            if path.name in resolve_exclusions():
                continue

            # O critério de "é um Planet": estar DIRETAMENTE abaixo de
            # um segmento `planets`. É o `parent` que decide, e não o
            # caminho inteiro — por isso o mesmo teste vale para os dois
            # layouts conhecidos.
            if path.parent.name != self.PLANETS_SEGMENT:
                continue

            planets.append(
                self._describe(path)
            )

        return planets

    def _describe(self, path: Path) -> PlanetStructure:
        """
        Descreve a raiz de um Planet: arquivos e diretórios.
        """

        files: set[str] = set()
        directories: set[str] = set()

        # Só a RAIZ do Planet (`iterdir`, e não `walk`): a regra SOLAR-ROF-006
        # exige peças no primeiro nível, e descer descreveria outra
        # coisa.
        for entry in path.iterdir():

            if entry.name in self.IGNORED_DIRECTORIES:
                continue

            # Arquivo e diretório vão para conjuntos SEPARADOS: é essa
            # separação que faz um `repository.py` solto não satisfazer
            # o diretório `repository/`.
            if entry.is_dir():
                directories.add(entry.name)
            else:
                files.add(entry.name)

        return PlanetStructure(
            name=path.name,
            path=path.relative_to(self.root).as_posix(),
            files=frozenset(files),
            directories=frozenset(directories)
        )
