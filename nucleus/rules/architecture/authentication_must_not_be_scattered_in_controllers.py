# SOLAR-SEG-006 — a DISPERSÃO das verificações de autenticação.
#
# Complementa a SOLAR-SEG-003, e a diferença entre as duas é o alvo:
#
#     SOLAR-SEG-003   a IMPLEMENTAÇÃO (o Controller importar `jwt`, `hashlib`,
#           `jose`, ...);
#     SOLAR-SEG-006   a DISPERSÃO (o Controller conferir `current_user`,
#           chamar `abort(401)`, decidir permissão).
#
# Dá para passar na SOLAR-SEG-003 e falhar na SOLAR-SEG-006: um Controller que não
# implementa nada de criptografia, mas decide quem entra em cada
# método, delegou a criptografia e ficou com a autorização.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import SECURITY, Rule, rule_code
from nucleus.rules.scanner.controller_auth_checks import (
    ControllerAuthChecks
)


class AuthenticationMustNotBeScatteredInControllers(Rule):
    """
    Regra arquitetural:

    SOLAR-SEG-006

    A autenticação NÃO deve ficar espalhada pelos Controllers.

    É VIOLAÇÃO:

        class DocumentController:

            def list(self):
                if not current_user.is_authenticated:      ❌
                    abort(401)                              ❌

            def delete(self, id):
                if not has_permission("delete"):            ❌
                    abort(403)                              ❌

    Correto — a autenticação acontece ANTES, na arquitetura:

        class DocumentController:

            @staticmethod
            def list():
                # Nenhuma verificação de sessão aqui: quem decide
                # quem entra é o middleware, antes do Controller.
                output = list_documents_use_case().execute()
                return DocumentResource.to_object(output)

    A verificação pertence:

        - aos componentes de segurança (nucleus.security);
        - ao middleware/configuração da Atmosphere.

    O Controller apenas PARTICIPA do fluxo: recebe o pedido já
    autenticado e delega ao UseCase.

    Complementa a SOLAR-SEG-003 (que barra a IMPLEMENTAÇÃO de
    autenticação): aqui o alvo é a DISPERSÃO das verificações.

    O contexto desta regra é um ControllerAuthChecks.
    """

    def code(self) -> str:
        return rule_code(SECURITY, 6)

    def description(self) -> str:
        return (
            "Autenticação não deve ficar espalhada pelos "
            "Controllers."
        )

    def validate(self, usage: ControllerAuthChecks) -> None:

        # Conjunto vazio é o caso correto — e o único que passa. A
        # regra não tenta medir "quantas verificações é demais":
        # qualquer uma já é responsabilidade que não é do Controller.
        if not usage.checks:
            return

        raise SolarException(
            self._build_message(usage)
        )

    def _build_message(
        self,
        usage: ControllerAuthChecks
    ) -> str:

        # `sorted` porque `checks` é um conjunto e conjunto não tem
        # ordem: sem isso, a mesma violação sairia com as
        # verificações trocadas de posição a cada execução.
        return (
            f"{self.code()}: "
            f"o Controller '{usage.controller}' "
            f"({usage.file}:{usage.line}) verifica autenticação "
            f"diretamente ({', '.join(sorted(usage.checks))}). "
            f"A autenticação deve ficar nos componentes de segurança "
            f"(nucleus.security) e no middleware, não espalhada pelo "
            f"Controller."
        )
