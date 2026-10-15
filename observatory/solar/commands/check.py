"""
Comando `check`: verifica as regras arquiteturais no projeto.

    python observatory/solar check [caminho]

Sem caminho, verifica o diretório atual.

Códigos de saída:

    0   resultado `correct`
    1   resultado `violation`
    2   o caminho informado não existe

O código de saída é o que faz uma esteira de integração contínua
REPROVAR o build; os status em palavra (`correct` / `violation`)
são o que a pessoa lê.

TODA verificação é registrada em Markdown dentro de
`observatory/solar/check/` — ver `audit.py`.
"""

import sys
from pathlib import Path

from nucleus.rules.project_validator import ProjectValidator
from observatory.solar import audit


CLEAN = 0
VIOLATIONS = 1
INVALID_ROOT = 2

HELP_FLAGS = ("-h", "--help")

USAGE = (
    "uso: python observatory/solar check [caminho]\n"
    "\n"
    "Verifica as regras arquiteturais da SOLAR no projeto.\n"
    "Sem caminho, verifica o diretório atual."
)


def run_check(arguments) -> int:
    """
    Executa a verificação e devolve o código de saída.
    """

    # `list()`: os argumentos podem chegar como qualquer iterável (a
    # CLI passa uma tupla) e abaixo eles são percorridos duas vezes.
    arguments = list(arguments)

    # `--help` vence qualquer outra coisa, inclusive um caminho
    # inválido: quem pediu ajuda quer a ajuda.
    if any(flag in arguments for flag in HELP_FLAGS):
        print(USAGE)
        return CLEAN

    # Caminho ausente significa "o projeto atual", que é o uso
    # normal dentro do repositório.
    root = Path(arguments[0]) if arguments else Path.cwd()

    # Conferir ANTES de varrer: sem isso, um diretório inexistente
    # devolveria relatório vazio (o que não existe não tem
    # violação) e a esteira passaria com `correct` sem ter
    # verificado nada.
    if not root.is_dir():
        print(f"caminho inválido: {root}", file=sys.stderr)
        return INVALID_ROOT

    report = ProjectValidator(root).validate()

    print(report)

    # Registra ANTES de devolver o código: a violação precisa ficar
    # no histórico, e é justamente a execução que falha que alguém
    # vai querer revisar depois.
    _announce(audit.record(report, root))

    return CLEAN if report.is_clean() else VIOLATIONS


def _announce(path: Path) -> None:
    """
    Informa onde ficou o registro da verificação.
    """

    # A formatação do caminho vem do módulo de auditoria: a subida do
    # servidor, que também registra quando há violação, mostra o
    # caminho da mesma forma.
    print(f"auditoria: {audit.display_path(path)}")
