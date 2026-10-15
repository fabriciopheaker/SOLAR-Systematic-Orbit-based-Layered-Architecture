# Acumulador de erros de validação.
#
# Existe para o Validator poder relatar VÁRIOS problemas de uma vez:
# devolver um erro por requisição obrigaria o cliente a tentar de
# novo para descobrir o segundo.
class Notification:

    def __init__(self):
        # Lista de dicts, e não de exceções: o conteúdo é dado de
        # resposta, serializável direto, sem conversão no caminho.
        self.errors = []

    def add(self, code: str, message: str, field: str | None = None) -> None:
        # `field` é opcional porque há erro que não é de campo — o
        # corpo inteiro ausente, por exemplo.
        self.errors.append({
            "code": code,
            "message": message,
            "field": field
        })

    def has_errors(self) -> bool:
        # Pergunta separada de `all()`: quem só quer saber se passou
        # não precisa receber a lista.
        return len(self.errors) > 0

    def all(self) -> list:
        # A lista INTERNA, sem cópia: o Notification é montado e
        # consumido dentro da mesma requisição e não sobrevive a ela.
        return self.errors

    def clear(self) -> None:
        # `clear()` e não `self.errors = []`: quem já guardou a
        # referência da lista continua enxergando o estado atual.
        self.errors.clear()