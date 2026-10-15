"""
Linha de comando da SOLAR.

    python observatory/solar check [caminho]

Cada comando é uma função que recebe os argumentos restantes e
devolve o CÓDIGO DE SAÍDA — quem chama não precisa saber mais
nada sobre ele.
"""

import sys

from observatory.solar.commands.check import run_check


# Registro dos comandos. O valor é a FUNÇÃO que executa, e o contrato
# dela é devolver o código de saída — quem despacha não precisa saber
# mais nada sobre o comando.
COMMANDS = {
    "check": run_check,
}

USAGE = (
    "uso: python observatory/solar <comando> [argumentos]\n"
    "\n"
    "Comandos:\n"
    "  check [caminho]   verifica as regras arquiteturais no\n"
    "                    projeto (sem caminho, o diretório atual)\n"
    "\n"
    "Exemplos:\n"
    "  python observatory/solar check\n"
    "  python observatory/solar check ./meu-projeto"
)

HELP_FLAGS = ("-h", "--help", "help")

CLEAN = 0
UNKNOWN_COMMAND = 2


def main(argv=None) -> int:
    """
    Despacha o comando e devolve o código de saída.
    """

    # `argv` injetável para o teste chamar `main(["check", ...])` sem
    # mexer em `sys.argv`; sem ele, usa os argumentos do processo.
    arguments = list(sys.argv[1:] if argv is None else argv)

    # A ajuda global só vale na PRIMEIRA posição: `solar check
    # --help` pertence ao comando `check`, não a quem despacha.
    if not arguments or arguments[0] in HELP_FLAGS:
        print(USAGE)
        return CLEAN

    # `.get` e não `[...]`: o comando desconhecido tem tratamento
    # próprio logo abaixo, com mensagem na saída de ERRO.
    command = arguments[0]
    handler = COMMANDS.get(command)

    if handler is None:
        print(f"comando desconhecido: {command}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return UNKNOWN_COMMAND

    # `arguments[1:]` e não `arguments`: o comando já foi consumido, e o
    # que sobra é do handler (o `check` recebe o caminho, se houver).
    return handler(arguments[1:])
