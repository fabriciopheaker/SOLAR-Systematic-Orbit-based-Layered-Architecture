import ast

from nucleus.rules.scanner.secret_patterns import PLACEHOLDER_PREFIX


# Marcador explícito de exceção (opt-out).
#
# Fica no próprio código, na linha do literal ou na linha acima,
# e é revisável no pull request — diferente de um ignore escondido
# em arquivo de configuração:
#
#     # solar:allow-secret   (nome da chave no ambiente, não o valor)
#     SECRET_KEY = "SECRET_KEY"
SUPPRESSION_MARKER = "solar:allow-secret"


def is_suppressed(
    node: ast.Constant,
    lines: list[str],
    marker: str = SUPPRESSION_MARKER
) -> bool:
    """
    Indica se o literal está anotado com o marcador de exceção.

    Vale o marcador na própria linha, em qualquer linha do literal
    (texto de várias linhas) ou na linha imediatamente acima —
    este último caso é o comentário que precede o código.

    A linha ACIMA só libera se for um comentário DEDICADO. Sem
    isso, `OUTRA = 1  # solar:allow-secret` liberaria o código da
    linha seguinte, e a exceção viraria um ignore escondido.
    """

    start = max(1, node.lineno - 1)
    end = node.end_lineno or node.lineno

    for number in range(start, end + 1):

        if number > len(lines):
            break

        line = lines[number - 1]

        if marker not in line:
            continue

        if number < node.lineno and not line.strip().startswith("#"):
            continue

        return True

    return False


def is_default(
    value: str,
    prefix: str = PLACEHOLDER_PREFIX
) -> bool:
    """
    Indica se o valor é um DEFAULT que espera vir do ambiente.

    Convenção do projeto: um valor que COMEÇA com o prefixo não é
    um segredo — é a marca de "campo vazio, o valor real vem do
    ambiente":

        DATABASE_PASSWORD = "SOLAR_DEFAULT"
        SECRET_KEY = "SOLAR_DEFAULT"

    Sem essa marca, todo campo de configuração com valor de
    partida vira falso positivo, e a reação natural é desligar a
    regra.
    """

    return bool(value) and value.startswith(prefix)
