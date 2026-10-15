# SOLAR-ARCH-023 — segredo reconhecido pelo CONTEÚDO.
#
# Irmã da SOLAR-ARCH-020, e a diferença é o que cada uma olha:
#
#     020   o NOME da variável (SECRET_KEY, password, ...)
#     023   o VALOR — pega o segredo mesmo com nome inofensivo
#           (CHAVE = "AKIA...")
#
# As duas podem apontar para o mesmo trecho. São regras separadas
# porque a 020 não enxerga segredo de nome neutro, e a 023 não
# enxerga segredo que não case com nenhum padrão conhecido.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import Rule
from nucleus.rules.scanner.secret_occurrence import SecretOccurrence


class SecretsMustNotAppearInSource(Rule):
    """
    Regra arquitetural:

    SOLAR-ARCH-023

    Secrets NÃO podem estar no código-fonte.

    Diferente da SOLAR-ARCH-020 — que detecta pelo NOME da
    variável (SECRET_KEY, password, ...) — esta regra detecta pelo
    CONTEÚDO: o segredo é reconhecido mesmo que o nome seja
    inofensivo.

    É VIOLAÇÃO:

        CHAVE = "AKIAIOSFODNN7EXAMPLE"                  ❌
        HEADER = "-----BEGIN RSA PRIVATE KEY-----"      ❌
        TOKEN = "ghp_0123456789012345678901234567"      ❌
        JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.x"  ❌

    O segredo pertence ao Environment, e o código o obtém de lá:

        CHAVE = os.environ["AWS_ACCESS_KEY_ID"]         ✅
        CHAVE = environment.get("AWS_ACCESS_KEY_ID")    ✅

    Um casamento de padrão, porém, NÃO prova que existe segredo: o
    scanner também marca os locais que exigem contexto. Estes são
    ignorados, e cada um pode ser desligado no construtor:

        documentation   docstring/texto solto — não é valor usado
                        pelo programa (ignore_documentation);
        example         valor de exemplo/placeholder conhecido
                        (ignore_examples);
        suppressed      trecho anotado com "solar:allow-secret"
                        (ignore_suppressed).

    A exceção fica VISÍVEL no código e é revisável no pull
    request — nenhuma delas é um ignore escondido em arquivo de
    configuração.

    O valor do segredo NÃO é registrado na mensagem: reportar o
    valor transformaria o relatório em um novo vazamento.

    O contexto desta regra é um SecretOccurrence.
    """

    def __init__(
        self,
        ignore_documentation: bool = True,
        ignore_examples: bool = True,
        ignore_suppressed: bool = True
    ):
        # Desligáveis porque cada uma troca rigor por ruído: com
        # `ignore_examples=False`, todo placeholder do próprio
        # manual viraria violação.
        self.ignore_documentation = ignore_documentation
        self.ignore_examples = ignore_examples
        self.ignore_suppressed = ignore_suppressed

    def code(self) -> str:
        return "SOLAR-ARCH-023"

    def description(self) -> str:
        return "Secrets não podem estar no código-fonte."

    def validate(self, occurrence: SecretOccurrence) -> None:

        # A justificativa é avaliada AQUI, e não no scanner: o
        # scanner DESCREVE ("é docstring", "é exemplo"); decidir o
        # que fazer com essa informação é política, e política é da
        # regra.
        if self._is_justified(occurrence):
            return

        raise SolarException(
            self._build_message(occurrence)
        )

    def _is_justified(self, occurrence: SecretOccurrence) -> bool:
        """
        Indica se a ocorrência tem justificativa para ser ignorada.
        """

        # `or` encadeado: basta UMA justificativa. E cada termo
        # começa pela flag, porque com ela desligada a
        # justificativa não vale — é assim que "não ignorar
        # exemplos" transforma exemplo em violação.
        return (
            self.ignore_documentation and occurrence.documentation
        ) or (
            self.ignore_examples and occurrence.example
        ) or (
            self.ignore_suppressed and occurrence.suppressed
        )

    def _build_message(
        self,
        occurrence: SecretOccurrence
    ) -> str:

        # O local e o TIPO do padrão, nunca o valor: mensagem com o
        # segredo dentro viraria um novo vazamento — no terminal,
        # no log e no arquivo de auditoria.
        return (
            f"{self.code()}: "
            f"segredo do tipo '{occurrence.pattern}' encontrado em "
            f"{occurrence.file}:{occurrence.line}. "
            f"Secrets devem vir do Environment e nunca do "
            f"código-fonte. (o valor não é exibido por segurança)"
        )
