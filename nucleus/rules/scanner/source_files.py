"""
Quais arquivos são CÓDIGO DO PROJETO.

Nem todo `.py` sob a raiz participa da arquitetura.

Os TESTES são o caso que motiva este módulo: para validar um
comportamento e descobrir falhas, um teste precisa justamente
quebrar as regras — importar a ORM direto, montar um SQL na mão,
declarar um Model na hora. Cobrar arquitetura de teste é cobrar
do lugar errado, e o resultado é a regra ficar vermelha por causa
de um `assert`.

Por isso a exclusão acontece no SCANNER, não na Rule: o arquivo de
teste nem chega a ser interpretado.

Diretórios técnicos (cache, ambiente virtual, build) saem pelo
mesmo caminho, e por um motivo mais simples: não são código
escrito à mão.

O escopo é por DIRETÓRIO, não por nome de arquivo: um `tests.py`
continua sendo analisado — é um arquivo como outro qualquer. A
exceção são os nomes que SÃO infraestrutura de teste em qualquer
lugar (`conftest.py`, `test_*.py`, `*_test.py`).
"""

from collections.abc import Iterable
from pathlib import Path


# Diretórios que NÃO são código do projeto.
DEFAULT_EXCLUDED_DIRECTORIES = frozenset({
    # Técnicos: cache, ambiente virtual, artefato de build.
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
    # Testes e material de apoio: quebrar a regra aqui é legítimo.
    "examples",
    "fixtures",
    "samples",
    "spec",
    "specs",
    "test",
    "tests",
})

# Nomes que são infraestrutura de teste ONDE QUER QUE ESTEJAM.
#
# Três formatos porque não existe um só: `conftest.py` (nome do
# pytest), `test_*.py` (prefixo, o usado neste projeto) e `*_test.py`
# (sufixo, comum em outros). Sem os três, um teste fora de `tests/`
# voltaria a ser cobrado pela arquitetura.
TEST_FILENAMES = frozenset({
    "conftest.py",
})

TEST_FILENAME_PREFIXES = (
    "test_",
)

TEST_FILENAME_SUFFIXES = (
    "_test.py",
)


def source_files(
    root: Path,
    excluded_directories: Iterable[str] | None = None
) -> list[Path]:
    """
    Arquivos `.py` que fazem parte do projeto, em ordem.
    """

    # `resolve()` UMA vez, e a MESMA raiz passada adiante: se cada
    # chamada resolvesse de novo, `relative_to` poderia comparar
    # caminhos escritos de formas diferentes no Windows.
    resolved = Path(root).resolve()

    # `sorted` no `rglob`: a ORDEM tem que ser estável. Sem ela, dois
    # arquivos poderiam alternar de posição entre execuções e o
    # relatório sairia diferente a cada rodada.
    return [
        file
        for file in sorted(resolved.rglob("*.py"))
        if belongs_to_project(file, resolved, excluded_directories)
    ]


def belongs_to_project(
    file: Path,
    root: Path,
    excluded_directories: Iterable[str] | None = None
) -> bool:
    """
    Indica se o arquivo participa da arquitetura.
    """

    # Nome primeiro: é a checagem mais barata e a que vale em qualquer
    # lugar do projeto.
    if is_test_file(file.name):
        return False

    return not is_inside_excluded(
        file,
        root,
        excluded_directories
    )


def is_test_file(name: str) -> bool:
    """
    Indica se o nome é de um arquivo de teste.
    """

    # Os três em `or`: qualquer um basta. `startswith`/`endswith`
    # aceitam TUPLA, então os formatos ficam em constantes e ampliar é
    # editar a lista.
    return (
        name in TEST_FILENAMES
        or name.startswith(TEST_FILENAME_PREFIXES)
        or name.endswith(TEST_FILENAME_SUFFIXES)
    )


def is_inside_excluded(
    path: Path,
    root: Path,
    excluded_directories: Iterable[str] | None = None
) -> bool:
    """
    Indica se o caminho está sob um diretório excluído.

    Olha só os DIRETÓRIOS entre a raiz e o próprio caminho.
    """

    # Resolvido AQUI e não recebido pronto: a função é pública e pode
    # ser chamada direto — o `PlanetScanner` faz exatamente isso.
    excluded = resolve_exclusions(excluded_directories)

    # `parts[:-1]` — só os DIRETÓRIOS do caminho. O último elemento é o
    # próprio arquivo, e um arquivo chamado `tests.py` não é o
    # diretório `tests`.
    return any(
        directory in excluded
        for directory in Path(path).relative_to(root).parts[:-1]
    )


def resolve_exclusions(
    excluded_directories: Iterable[str] | None = None
) -> frozenset[str]:
    """
    Exclusões em vigor.

    `None` usa o padrão; uma coleção (mesmo vazia) substitui o
    padrão — é assim que um scanner permite desligar a exclusão.
    """

    # `is None` e não `if not ...`: coleção VAZIA é uma escolha ("não
    # exclua nada"). Tratá-la como "sem argumento" tiraria a
    # possibilidade de um scanner varrer tudo.
    if excluded_directories is None:
        return DEFAULT_EXCLUDED_DIRECTORIES

    return frozenset(excluded_directories)
