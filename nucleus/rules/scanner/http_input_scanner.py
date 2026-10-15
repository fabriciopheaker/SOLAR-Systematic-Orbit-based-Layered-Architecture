# Scanner das ENTRADAS HTTP.
#
# A entrada não tem um lugar próprio no código: ela é declarada JUNTO DA
# ROTA, nos keywords do `add_url_rule`. Por isso este scanner lê as
# chamadas de registro de rota e monta um `HttpInput` por MÉTODO.
#
# Análise ESTÁTICA: os guardas chegam como NOME (`FileSanitizer`), não
# como instância — o contrato aceita os dois (ver `HttpInput`).
import ast
from pathlib import Path

from nucleus.contracts.http_input import HttpInput
from nucleus.rules.scanner.routing_convention import (
    RoutingConvention,
    flask_routing_convention,
    is_super_delegation,
)
from nucleus.rules.scanner.source_files import source_files


class HttpInputScanner:
    """
    Scanner responsável por identificar as ENTRADAS HTTP
    declaradas no código-fonte e descrever o contrato de cada uma.

    A rota diz para onde a requisição vai E quem pode entrar — os
    guardas são declarados NELA:

        # planets/example/routes.py
        blueprint.add_url_rule(
            "/users",
            "create_example_user",
            CreateUserController.create,
            methods=["POST"],
            sanitizer=CreateUserSanitizer,
            validator=CreateUserValidator,
        )

    O scanner responde:

        "Cada entrada que transporta dados tem guarda declarado?"

    O scanner NÃO decide se a entrada é válida: isso é
    responsabilidade da Rule SOLAR-ARCH-013.

    VALIDAÇÃO ESTÁTICA: como o scanner encontra apenas os NOMES
    das implementações (ex.: "CreateUserSanitizer"), o HttpInput
    produzido carrega esses nomes. A existência do pipeline é o
    que a regra verifica.

    A detecção é guiada por uma RoutingConvention, o que mantém
    o scanner desacoplado do framework (Flask, hoje).
    """

    # Métodos HTTP que aceitam CORPO. Uma rota com um destes
    # métodos é tratada como entrada que TRANSPORTA DADOS, mesmo
    # sem content_type declarado — fechando a brecha de omitir o
    # tipo de conteúdo para escapar da SOLAR-ARCH-013.
    #
    # `GET` e `DELETE` ficam de fora: por convenção não levam corpo, e
    # tratá-los como entrada de dados acusaria toda rota de leitura.
    BODY_METHODS = frozenset({
        "POST",
        "PUT",
        "PATCH",
    })

    # Nomes de keyword argument lidos na declaração da rota. Constantes
    # em vez de literais espalhados: são o CONTRATO entre o scanner e
    # quem declara as rotas.
    METHODS_KEYWORD = "methods"

    # Os keywords que DECLARAM a proteção da entrada. São eles que a
    # SOLAR-ARCH-013 cobra: a rota diz quem limpa e quem exige.
    SANITIZER_KEYWORD = "sanitizer"
    VALIDATOR_KEYWORD = "validator"

    # Método padrão do Flask quando `methods` não é declarado.
    #
    # Chutar o contrário (`POST`) faria toda rota sem `methods` virar
    # entrada de dados — e a regra acusaria rota de leitura.
    DEFAULT_METHOD = "GET"

    def __init__(
        self,
        root: Path,
        convention: RoutingConvention | None = None
    ):
        self.root = root.resolve()

        # Injetável, com o Flask como PADRÃO: o teste passa uma
        # convenção própria para provar que o scanner não conhece o
        # framework.
        self.convention = (
            convention or flask_routing_convention()
        )

    def scan(self) -> list[HttpInput]:
        """
        Percorre o projeto e retorna as entradas HTTP declaradas.
        """

        inputs: list[HttpInput] = []

        for file in source_files(self.root):

            inputs.extend(
                self._scan_file(file)
            )

        return inputs

    def _scan_file(self, file: Path) -> list[HttpInput]:
        """
        Analisa um único arquivo Python.

        O código NÃO é executado: a análise é feita sobre a AST.
        """

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        inputs: list[HttpInput] = []

        # Só CHAMADA, e só a de REGISTRO de rota. Rota por decorator
        # não é lida aqui — ela já é violação da SOLAR-ARCH-016.
        for node in ast.walk(tree):

            if not isinstance(node, ast.Call):
                continue

            # `super().add_url_rule(...)` é a DELEGAÇÃO de um mecanismo
            # que estende o framework, e não a declaração de uma rota.
            if is_super_delegation(node):
                continue

            mechanism = self._callable_name(node.func)

            if mechanism not in self.convention.route_registrations:
                continue

            inputs.extend(
                self._declarations(node)
            )

        return inputs

    def _declarations(self, node: ast.Call) -> list[HttpInput]:
        """
        Descreve a entrada HTTP de um registro de rota.

        Uma rota pode declarar vários métodos; cada método é uma
        entrada HTTP distinta.
        """

        # O PRIMEIRO argumento posicional é a ROTA (`"/documents"`).
        # `node.args` pode estar vazio — daí o marcador, para a mensagem
        # não sair com um buraco.
        name = self._text(node.args[0]) if node.args else "<unknown>"

        # QUEM PROTEGE a entrada é declarado na PRÓPRIA rota, e é o que
        # esta leitura pega.
        sanitizer = self._guard_name(
            node,
            self.SANITIZER_KEYWORD
        )

        validator = self._guard_name(
            node,
            self.VALIDATOR_KEYWORD
        )

        # UMA entrada por MÉTODO: `methods=["GET", "POST"]` são duas
        # entradas diferentes — uma transporta dados e a outra não —, e
        # a regra precisa poder julgá-las separadamente.
        return [
            HttpInput(
                method=method,
                name=name,
                sanitizer=sanitizer,
                validator=validator,
                # `carries_data` explícito: é o scanner afirmando o que
                # a análise estática consegue saber (ver `_carries_data`).
                carries_data=self._carries_data(
                    method,
                    sanitizer is not None or validator is not None
                )
            )
            for method in self._methods(node)
        ]

    def _guard_name(
        self,
        node: ast.Call,
        keyword: str
    ) -> str | None:
        """
        O NOME do guarda declarado na rota.

            sanitizer=CreateUserSanitizer    → "CreateUserSanitizer"
            sanitizer=CreateUserSanitizer()  → "CreateUserSanitizer"

        Declara-se a CLASSE ou a INSTÂNCIA (é ela que executa); o que
        a análise estática guarda é o nome da implementação.
        """

        for option in node.keywords:

            if option.arg != keyword:
                continue

            value = option.value

            if isinstance(value, ast.Call):
                value = value.func

            return self._text(value)

        return None

    def _methods(self, node: ast.Call) -> list[str]:
        """
        Lê o keyword `methods` (ex.: methods=["POST"]).

        Quando ausente, assume o método padrão do framework.
        """

        for keyword in node.keywords:

            if keyword.arg != self.METHODS_KEYWORD:
                continue

            # `methods` declarado, mas com expressão não literal
            # (`methods=METHODS`): não dá para saber quais são.
            if not isinstance(keyword.value, ast.List):
                break

            # `if self._text(element)` descarta o que não virou texto —
            # elemento não literal não contribui.
            methods = [
                self._text(element)
                for element in keyword.value.elts
                if self._text(element)
            ]

            if methods:
                return methods

            # Lista vazia (`methods=[]`): cai no padrão abaixo.
            break

        # Sem `methods` utilizável: o padrão do framework.
        return [self.DEFAULT_METHOD]

    def _text(self, node: ast.AST) -> str | None:
        """
        Converte uma expressão da AST em texto.

        Literais retornam o próprio valor; demais expressões
        retornam o código-fonte correspondente.
        """

        # Literal de TEXTO devolve o valor cru, sem aspas — é o que vira
        # `content_type` e o nome do sanitizer no contexto.
        if isinstance(node, ast.Constant):

            if isinstance(node.value, str):
                return node.value

            # Literal de outro tipo (número, `True`): o texto dele.
            return str(node.value)

        # Nome de classe (`FileSanitizer`) e demais expressões: o texto
        # do código-fonte. É assim que o NOME do guarda chega ao
        # contexto na análise estática.
        return ast.unparse(node)

    def _carries_data(
        self,
        method: str,
        has_guard: bool
    ) -> bool:
        """
        Decide se a entrada transporta dados externos.

        O critério estático é: a ROTA declarou guarda OU o método
        aceita corpo. Assim, uma rota POST sem guarda continua sendo
        tratada como entrada de dados (e não escapa da regra), e uma
        entrada com guarda declarado é tratada como entrada mesmo que
        o método não estivesse na lista.
        """

        # Guarda declarado JÁ É a rota dizendo "por aqui passam
        # dados" — o mesmo `carries_data=True` que a Atmosphere afirma
        # em execução.
        if has_guard:
            return True

        # `strip().upper()`: `methods=["post"]` e `methods=["POST"]` são
        # o mesmo método, e o conjunto está em maiúsculas.
        return method.strip().upper() in self.BODY_METHODS

    def _callable_name(self, node: ast.AST) -> str | None:
        """
        Retorna o nome de um chamável.

            blueprint.add_url_rule(...) → "add_url_rule"
            add_url_rule(...)           → "add_url_rule"
        """

        # O chamável pode chegar já aplicado (`Call`) ou como nome solto.
        if isinstance(node, ast.Call):
            node = node.func

        # `blueprint.add_url_rule` → o que interessa é o ÚLTIMO nome; o
        # objeto não entra na decisão, porque a convenção olha só o
        # vocabulário.
        if isinstance(node, ast.Attribute):
            return node.attr

        if isinstance(node, ast.Name):
            return node.id

        return None
