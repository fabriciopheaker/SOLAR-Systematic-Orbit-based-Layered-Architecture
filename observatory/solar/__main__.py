"""
Permite executar a verificação como comando:

    python observatory/solar check

O diretório do projeto entra no `sys.path` antes de qualquer import
da arquitetura: ao executar um DIRETÓRIO, o Python aponta o
`sys.path` para dentro dele — não para a raiz do projeto. Sem este
ajuste, `import nucleus` não funcionaria.

A raiz é encontrada subindo a partir deste arquivo até o diretório
que contém `nucleus/`, e não por uma quantidade fixa de níveis:
assim mover o comando de lugar não quebra o comando.
"""

import sys
from pathlib import Path


def project_root() -> Path:
    """
    Diretório do projeto SOLAR (o que contém `nucleus/`).
    """

    # Marcador do projeto: o diretório que tem `nucleus/` é a raiz.
    # `parents` sobe nível a nível, e não em quantidade fixa: mover
    # o comando de pasta não quebra a descoberta.
    for parent in Path(__file__).resolve().parents:

        if (parent / "nucleus").is_dir():
            return parent

    # Nenhum ancestral tem `nucleus/`: devolve um diretório
    # previsível em vez de estourar. Se isso acontecer, o erro vai
    # aparecer no import de `nucleus`, com mensagem clara.
    return Path(__file__).resolve().parent


PROJECT_ROOT = project_root()

# Calculado UMA vez, no import: `sys.path` é global do processo, e
# repetir a inserção a cada chamada acumularia entradas iguais.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Import DEPOIS do ajuste de `sys.path` — é por isso que o
# `# noqa: E402` está aqui: sem o ajuste, `nucleus` não resolve.
from observatory.solar.cli import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
