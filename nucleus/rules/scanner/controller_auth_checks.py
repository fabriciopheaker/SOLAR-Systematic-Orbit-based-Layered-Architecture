# Contexto da SOLAR-SEG-006: verificação de autenticação feita
# DENTRO do Controller.
#
# Autenticação pertence ao `nucleus.security` e ao middleware. Um
# Controller que confere `current_user` ou chama `abort(401)`
# assumiu uma responsabilidade que não é dele.
from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerAuthChecks:
    """
    Descreve as VERIFICAÇÕES DE AUTENTICAÇÃO encontradas no corpo
    de um Controller.

    O ControllerAuthCheckScanner produz esta estrutura para cada
    Controller — uma classe terminada em "Controller" DENTRO de um
    módulo de Controller (ver `controller_module`):

        controller = "AuthController"
        checks     = {"current_user", "abort(401)"}

    A autenticação/autorização pertence aos componentes de
    segurança da arquitetura (nucleus.security) e ao middleware —
    não ao Controller.

    checks:
        Verificações de autenticação usadas (vazio quando o
        Controller não as espalha).

    file / line:
        Local da declaração da classe.
    """

    controller: str

    # Conjunto vazio significa "este Controller não espalha
    # autenticação" — que é o caso correto, e o único que passa.
    checks: frozenset[str]

    file: str
    line: int
