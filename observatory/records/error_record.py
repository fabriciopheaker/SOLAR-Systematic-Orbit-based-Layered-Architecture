from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorRecord:
    """
    Um erro registrado pelo Observatório.

    number:
        Número da linha na tabela (0 antes de gravar).

    moment:
        Quando aconteceu, no fuso do Observatório.

    code:
        Código estável do erro (ex.: "INVALID_UPLOAD",
        "INTERNAL_ERROR").

    message:
        Mensagem GENÉRICA — a mesma que foi para o cliente.

    reference:
        Identificador do ocorrido; é o que liga a resposta ao
        registro.

    exception_type:
        Nome da classe da exceção (ex.: "ValidationException").

    detail:
        Rastro completo (traceback). Aqui o detalhe interno é
        bem-vindo: este banco é do Observatório, não é a resposta
        da API.

    method / route / status:
        Contexto da requisição, quando informado.

    solar_id / environment:
        Qual aplicação e em que ambiente o erro aconteceu.
    """

    # Ordem dos campos = ordem das colunas na tabela do
    # Observatório. Todos têm padrão vazio para que um registro
    # parcial (erro sem contexto de requisição, por exemplo) não
    # obrigue a preencher o que não se tem.
    moment: str
    code: str = ""
    message: str = ""
    reference: str = ""
    exception_type: str = ""
    # `detail` guarda o traceback COMPLETO, e aqui ele é
    # bem-vindo: este banco é do Observatório, não é a resposta da
    # API. É a contrapartida da SOLAR-SEG-008 — o detalhe interno
    # vai para o log, nunca para o cliente.
    detail: str = ""
    method: str = ""
    route: str = ""
    status: int = 0
    solar_id: str = ""
    environment: str = ""

    # `0` antes de gravar: quem numera é o banco (rowid), na
    # inserção. Um registro recém-montado ainda não tem número.
    number: int = 0
