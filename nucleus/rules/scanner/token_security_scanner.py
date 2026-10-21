# Scanner de uso de JWT/Token.
#
# DESCREVE as características de segurança de cada chamada — algoritmo
# declarado, verificação de assinatura, expiração. Não há julgamento
# aqui: a política é da SOLAR-SEG-007.
#
# `None` é resposta legítima em três momentos (o contexto guarda esse
# tri-estado): quando a informação não foi declarada, ou quando o
# payload não é literal e não dá para saber.
import ast
from pathlib import Path

from nucleus.rules.scanner.source_files import source_files
from nucleus.rules.scanner.token_usage import TokenUsage


class TokenSecurityScanner:
    """
    Scanner responsável por identificar os usos de JWT/Token no
    código-fonte e descrever as suas características de segurança.

    Reconhece:

        jwt.encode(payload, key, algorithm="HS256")
        jwt.decode(token, key, options={"verify_signature": False})
        jose.jwt.encode(payload, key, algorithm="none")

    Para cada uso, descreve:

        - o algoritmo declarado;
        - se a verificação de assinatura foi desativada;
        - se o payload emitido declara expiração ("exp").

    O scanner NÃO decide se há violação: isso é responsabilidade
    da Rule SOLAR-SEG-007.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    # Pacotes que expõem operações de token.
    #
    # Reconhecidos pelo nome em QUALQUER ponto da cadeia do chamável —
    # `jwt.encode` e `jose.jwt.encode` caem os dois (ver
    # `_knows_token_package`).
    TOKEN_PACKAGES = frozenset({"jwt", "jws"})

    # Operações de token.
    #
    # Só duas: emitir e ler. `get_unverified_header` e afins ficam
    # fora — o critério é o vocabulário da biblioteca, e ampliar é
    # editar esta constante.
    OPERATIONS = frozenset({"encode", "decode"})

    # Nomes de keyword argument, um por constante em vez de literais
    # espalhados: `jwt` e `jose` usam os MESMOS nomes, e ter a lista em
    # um lugar só deixa essa dependência à vista.
    ALGORITHM_KEYWORD = "algorithm"
    ALGORITHMS_KEYWORD = "algorithms"
    OPTIONS_KEYWORD = "options"
    PAYLOAD_KEYWORD = "payload"

    VERIFY_SIGNATURE_KEY = "verify_signature"
    EXPIRATION_KEY = "exp"

    def __init__(self, root: Path):
        self.root = root.resolve()

    def scan(self) -> list[TokenUsage]:
        """
        Percorre o projeto e descreve cada uso de token.
        """

        usages: list[TokenUsage] = []

        for file in source_files(self.root):

            usages.extend(
                self._scan_file(file)
            )

        return usages

    def _scan_file(self, file: Path) -> list[TokenUsage]:
        """
        Analisa um único arquivo Python.
        """

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        relative = file.relative_to(self.root).as_posix()

        usages: list[TokenUsage] = []

        # Só chamada interessa: uso de token é sempre `jwt.encode(...)`
        # ou `jwt.decode(...)`. `_operation` devolve `None` para
        # qualquer outro chamável, e o laço segue.
        for node in ast.walk(tree):

            if not isinstance(node, ast.Call):
                continue

            operation = self._operation(node.func)

            if operation is None:
                continue

            # A operação é calculada UMA vez e REPASSADA aos três
            # leitores: duas das perguntas só fazem sentido em um dos
            # sentidos — verificação de assinatura é da LEITURA, e
            # expiração é da EMISSÃO.
            usages.append(
                TokenUsage(
                    operation=operation,
                    algorithm=self._algorithm(node),
                    verifies_signature=self._verifies_signature(
                        node,
                        operation
                    ),
                    has_expiration=self._has_expiration(
                        node,
                        operation
                    ),
                    file=relative,
                    line=node.lineno
                )
            )

        return usages

    def _operation(self, func: ast.AST) -> str | None:
        """
        Identifica `jwt.encode` / `jwt.decode` (inclusive
        `jose.jwt.encode`).
        """

        # Precisa ser `algo.encode` / `algo.decode`.
        if not isinstance(func, ast.Attribute):
            return None

        if func.attr not in self.OPERATIONS:
            return None

        # E o objeto antes do ponto precisa ser (ou vir de) um pacote de
        # token. Sem esta checagem, um `codec.encode(...)` qualquer
        # viraria "uso de token".
        if not self._knows_token_package(func.value):
            return None

        return func.attr

    def _knows_token_package(self, node: ast.AST) -> bool:
        """
        Percorre a cadeia do chamável procurando o pacote de token.

            jwt            → True
            jose.jwt       → True
        """

        # Sobe a cadeia do chamável procurando o pacote em QUALQUER
        # posição: em `jose.jwt.encode`, `jwt` é o `attr` do meio.
        while isinstance(node, ast.Attribute):

            if node.attr in self.TOKEN_PACKAGES:
                return True

            node = node.value

        # A cadeia termina em um `Name` — é o caso de `jwt.encode`
        # direto, em que `jwt` é o próprio nome.
        return (
            isinstance(node, ast.Name)
            and node.id in self.TOKEN_PACKAGES
        )

    def _algorithm(self, node: ast.Call) -> str | None:
        """
        Lê o algoritmo declarado.

        Aceita tanto `algorithm="HS256"` quanto
        `algorithms=["HS256"]`.
        """

        # Primeiro a forma da EMISSÃO (`algorithm="HS256"`, um valor
        # só).
        value = self._keyword(node, self.ALGORITHM_KEYWORD)

        if value is not None:
            return self._text(value)

        # Depois a forma da LEITURA (`algorithms=["HS256"]`, uma
        # lista). Só o PRIMEIRO elemento: a regra julga o algoritmo
        # declarado, e a lista costuma trazer um.
        value = self._keyword(node, self.ALGORITHMS_KEYWORD)

        if isinstance(value, ast.List) and value.elts:
            return self._text(value.elts[0])

        return None

    def _verifies_signature(
        self,
        node: ast.Call,
        operation: str
    ) -> bool | None:
        """
        Detecta a DESATIVAÇÃO da verificação de assinatura.

        Só faz sentido em "decode".
        """

        # Só na LEITURA: `encode` não verifica assinatura — ele a
        # produz.
        if operation != "decode":
            return None

        # A flag vem dentro do dict de `options=`.
        options = self._keyword(node, self.OPTIONS_KEYWORD)

        if isinstance(options, ast.Dict):

            # `zip` de chaves com valores: na AST o dict é indexado por
            # posição, e chave e valor andam juntos.
            for key, value in zip(options.keys, options.values):

                # Chave não literal (`**kwargs`) não dá para julgar.
                if not isinstance(key, ast.Constant):
                    continue

                if key.value != self.VERIFY_SIGNATURE_KEY:
                    continue

                if isinstance(value, ast.Constant):
                    return bool(value.value)

        # `None` = não foi dito, e NÃO "está ligada": quem acusa é a
        # regra, e ela só acusa o `False` explícito.
        return None

    def _has_expiration(
        self,
        node: ast.Call,
        operation: str
    ) -> bool | None:
        """
        Verifica se o payload EMITIDO declara "exp".

        Só é possível quando o payload é um dicionário literal —
        caso contrário, a informação é desconhecida (None).
        """

        # Só na EMISSÃO: quem emite é que responde pela expiração.
        if operation != "encode":
            return None

        payload = self._payload(node)

        # Payload não literal (`payload` de variável, chamada): não dá
        # para saber o que tem dentro. `None` é a resposta honesta.
        if not isinstance(payload, ast.Dict):
            return None

        # Basta a CHAVE `exp` existir: o valor pode ser variável, e
        # declarar a chave já é declarar a intenção de expirar.
        return any(
            isinstance(key, ast.Constant)
            and key.value == self.EXPIRATION_KEY
            for key in payload.keys
        )

    def _payload(self, node: ast.Call) -> ast.AST | None:
        """
        Localiza o payload de um "encode".
        """

        # Forma NOMEADA primeiro (`payload=data`).
        keyword = self._keyword(node, self.PAYLOAD_KEYWORD)

        if keyword is not None:
            return keyword

        # Depois a POSICIONAL — no `jwt.encode`, o payload é o PRIMEIRO
        # argumento.
        if node.args:
            return node.args[0]

        return None

    def _keyword(
        self,
        node: ast.Call,
        name: str
    ) -> ast.AST | None:
        """
        Retorna o valor de um keyword argument.
        """

        # Varredura linear: as listas de keywords dos usos reais são
        # curtas, e montar um `dict` intermediário custaria mais do que
        # economiza. `keyword.arg` é `None` no `**kwargs`, e a
        # comparação com `name` já o descarta.
        for keyword in node.keywords:

            if keyword.arg == name:
                return keyword.value

        return None

    def _text(self, node: ast.AST) -> str | None:
        """
        Converte uma expressão em texto (literais devolvem o valor).
        """

        # `str(node.value)` e não `ast.unparse`: o literal já É o valor,
        # e o `str` normaliza para texto (a regra compara com `""` e
        # chama `lower()`).
        if isinstance(node, ast.Constant):
            return str(node.value)

        # Expressão (nome de variável, chamada) vira texto legível para
        # a mensagem da violação.
        return ast.unparse(node)
