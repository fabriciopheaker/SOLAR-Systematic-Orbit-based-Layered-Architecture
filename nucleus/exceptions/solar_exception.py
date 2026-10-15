

# Exceção base da SOLAR.
#
# É a raiz de todas as exceções da arquitetura — e é o que o
# ProjectValidator procura para transformar em violação do
# relatório: o que herda daqui é "violação de regra"; qualquer
# outro erro é bug e sobe como erro.
class SolarException(Exception):
    """
    Exceção base da arquitetura SOLAR.

    Todas as exceções específicas da SOLAR devem herdar desta classe,
    permitindo que a aplicação possa identificar e tratar de forma
    centralizada os erros pertencentes à arquitetura.
    """

    # `code` é opcional porque nem toda exceção tem código estável:
    # `ValidationException` monta o seu; outras só carregam a
    # mensagem. Quando não vem, `__str__` devolve a mensagem pura.
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code

    # O código prefixado é o que torna a mensagem útil fora de
    # contexto: "[INVALID_UPLOAD] ..." diz de que se trata sem
    # precisar do traceback ao lado.
    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"

        return self.message