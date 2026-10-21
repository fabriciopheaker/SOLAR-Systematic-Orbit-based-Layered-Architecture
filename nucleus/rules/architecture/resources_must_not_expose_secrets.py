from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import SECURITY, Rule, rule_code
from nucleus.rules.scanner.resource_exposure import ResourceExposure
from nucleus.rules.scanner.secret_names import is_secret_name


class ResourcesMustNotExposeSecrets(Rule):
    """
    Regra arquitetural:

    SOLAR-SEG-002

    Segredos NÃO podem ser retornados por Resources.

    Um Resource NÃO deve expor:

        password
        password_hash
        secret_key
        database_password
        tokens internos
        credenciais

    É VIOLAÇÃO:

        class UserResource(Resource):
            @classmethod
            def to_object(cls, data):
                return {
                    "id": data["id"],
                    "password": data["password"],        ❌
                    "password_hash": data["hash"],       ❌
                }

    Correto:

        class UserResource(Resource):
            @classmethod
            def to_object(cls, data):
                return {
                    "id": data["id"],
                    "name": data["name"],
                }

    O contexto desta regra é um ResourceExposure — diferente do
    contexto das regras de Dependency (SOLAR-RED-001 a SOLAR-RED-012).
    """

    def code(self) -> str:
        return rule_code(SECURITY, 2)

    def description(self) -> str:
        return "Segredos não podem ser retornados por Resources."

    def validate(self, exposure: ResourceExposure) -> None:

        # Reusa o vocabulário de `secret_names` da SOLAR-SEG-001: se
        # um nome não é sensível na ENTRADA, também não é na saída.
        # Uma lista separada aqui criaria duas verdades para a mesma
        # pergunta. `sorted` só para a mensagem ficar estável.
        leaked = sorted(
            field
            for field in exposure.fields
            if is_secret_name(field)
        )

        if not leaked:
            return

        raise SolarException(
            self._build_message(exposure, leaked)
        )

    def _build_message(
        self,
        exposure: ResourceExposure,
        leaked: list[str]
    ) -> str:

        # Nome dos CAMPOS, nunca o valor deles: a mensagem diz o que
        # estava sendo exposto, não o que os campos continham — e o
        # relatório circula.
        return (
            f"{self.code()}: "
            f"o Resource '{exposure.resource}' "
            f"({exposure.file}:{exposure.line}) expõe "
            f"{', '.join(leaked)}. "
            f"Segredos, credenciais e tokens internos não podem "
            f"ser retornados por Resources."
        )
