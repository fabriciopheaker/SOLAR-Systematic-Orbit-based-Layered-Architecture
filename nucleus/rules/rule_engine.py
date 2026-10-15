# O motor que aplica um conjunto de regras sobre um alvo.
#
# Um RuleEngine serve a UM contexto: o alvo que ele recebe tem que
# ser o que as suas regras sabem ler. Misturar contextos no mesmo
# motor quebra a execução — por isso cada Check do
# project_validator tem o seu.
#
# O project_validator não usa esta classe: ele chama as regras
# direto, porque precisa recolher TODAS as violações em vez de
# parar na primeira.
from nucleus.rules.rule import Rule


class RuleEngine:
    """
    Executa um conjunto de regras sobre um alvo.
    """

    def __init__(self, rules: list[Rule]):
        self.rules = rules

    def validate(self, target) -> None:
        """
        Executa todas as regras registradas
        sobre o alvo informado.
        """

        # Sem `try`, de propósito: a primeira violação interrompe.
        # O contrato deste motor é "validar ou levantar".
        for rule in self.rules:
            rule.validate(target)