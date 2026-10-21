# SOLAR-SEG-001 — segredo reconhecido pelo NOME.
#
# Par da SOLAR-SEG-004, que reconhece pelo CONTEÚDO. Aqui o gatilho é o
# nome do alvo (`SECRET_KEY`, `password`, ...) mais o valor ser um
# literal não vazio.
#
# ⚠️ O valor do segredo NÃO aparece na mensagem — ver `_build_message`.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import SECURITY, Rule, rule_code
from nucleus.rules.scanner.secret_literal import SecretLiteral
from nucleus.rules.scanner.secret_names import is_secret_name


class SecretsMustNotBeHardcoded(Rule):
    """
    Regra arquitetural:

    SOLAR-SEG-001

    Credenciais e segredos NÃO podem estar hardcoded no código.

    É VIOLAÇÃO:

        SECRET_KEY = "abc123"
        DATABASE_PASSWORD = "root"
        connect(password="root")
        API_TOKEN = "987654"

    NÃO é violação:

        SECRET_KEY = os.environ["SECRET_KEY"]
        DATABASE_PASSWORD = environment.get("DB_PASS")
        password = ""
        DATABASE_PASSWORD = "SOLAR_DEFAULT"      # default do ambiente
        # solar:allow-secret                      # exceção revisável
        SECRET_KEY = "SECRET_KEY"

    Segredos devem vir do Environment (variáveis de ambiente),
    nunca do código-fonte.

    O contexto desta regra é um SecretLiteral — diferente do
    contexto das regras de Dependency (SOLAR-RED-001 a SOLAR-RED-012).
    """

    def code(self) -> str:
        return rule_code(SECURITY, 1)

    def description(self) -> str:
        return (
            "Credenciais e segredos não podem estar hardcoded "
            "no código."
        )

    def validate(self, secret: SecretLiteral) -> None:

        # O scanner já filtra por nome; a regra reafirma a
        # POLÍTICA para poder ser usada isoladamente.
        if not is_secret_name(secret.name):
            return

        # Exceção explícita, visível e revisável no pull request:
        # o nome é sensível, mas o valor NÃO é segredo (nome de
        # chave do ambiente, código de erro).
        if secret.suppressed:
            return

        # Default marcado: o campo está vazio e espera o valor
        # vir do ambiente.
        if secret.default:
            return

        raise SolarException(
            self._build_message(secret)
        )

    def _build_message(self, secret: SecretLiteral) -> str:

        # Nome, arquivo e linha — o VALOR nunca: reportar o valor
        # transformaria o relatório (e o arquivo de auditoria) em um
        # novo vazamento.
        return (
            f"{self.code()}: "
            f"o valor de '{secret.name}' está hardcoded em "
            f"{secret.file}:{secret.line}. "
            f"Credenciais e segredos devem vir do Environment, "
            f"nunca do código-fonte."
        )
