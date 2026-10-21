from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import SECURITY, Rule, rule_code
from nucleus.rules.scanner.controller_security_usage import (
    ControllerSecurityUsage
)


class ControllerMustNotImplementAuthentication(Rule):
    """
    Regra arquitetural:

    SOLAR-SEG-003

    Controllers NÃO devem implementar autenticação diretamente.

    A autenticação/autorização deve utilizar os COMPONENTES DE
    SEGURANÇA definidos pela arquitetura (nucleus/security:
    identity, password, token).

    O Controller pode PARTICIPAR do fluxo, mas não deve virar o
    lugar onde ficam espalhadas as regras de autenticação — hash
    de senha, emissão/validação de token, criptografia.

    É VIOLAÇÃO:

        class AuthController:

            import jwt                        ❌
            import hashlib                    ❌
            import bcrypt                     ❌
            import secrets                    ❌

    Correto:

        class AuthController:

            from nucleus.security.token import Token      ✅
            from planets.auth.usecases.login import LoginUseCase  ✅

    A lista de módulos proibidos é uma CONSTANTE — ampliável
    conforme a arquitetura evoluir.

    O contexto desta regra é um ControllerSecurityUsage —
    diferente do contexto das regras de Dependency.
    """

    # Módulos que caracterizam autenticação/segurança
    # implementada DENTRO do Controller.
    FORBIDDEN_PACKAGES = frozenset({
        "hashlib",
        "bcrypt",
        "jwt",
        "jose",
        "secrets",
        "hmac",
        "passlib",
        "cryptography",
    })

    def code(self) -> str:
        return rule_code(SECURITY, 3)

    def description(self) -> str:
        return (
            "Controllers não devem implementar autenticação "
            "diretamente."
        )

    def validate(self, usage: ControllerSecurityUsage) -> None:

        # INTERSEÇÃO dos imports do arquivo com a lista proibida: só
        # o que está nos DOIS lados acusa. É por isso que
        # `nucleus.security.token` passa — o Controller pode USAR o
        # componente de segurança; o que ele não pode é implementar
        # um. `sorted` só para a mensagem ficar estável.
        offending = sorted(
            usage.imports & self.FORBIDDEN_PACKAGES
        )

        # Vazio = nenhum módulo proibido foi importado, que é o caso
        # correto.
        if not offending:
            return

        raise SolarException(
            self._build_message(usage, offending)
        )

    def _build_message(
        self,
        usage: ControllerSecurityUsage,
        offending: list[str]
    ) -> str:

        return (
            f"{self.code()}: "
            f"o Controller '{usage.controller}' "
            f"({usage.file}:{usage.line}) implementa autenticação "
            f"diretamente usando {', '.join(offending)}. "
            f"A autenticação deve utilizar os componentes de "
            f"segurança da arquitetura (nucleus.security), e não "
            f"regras espalhadas no Controller."
        )
