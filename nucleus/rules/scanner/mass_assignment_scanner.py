# Scanner de MASS ASSIGNMENT.
#
# O que ele procura é o `**`: um dicionário que chega de fora e
# preenche um contrato nomeado INTEIRO, sem que o código diga quais
# campos aceita. Há quatro formas de isso acontecer, e cada uma é uma
# função aqui — ver `EntityBinding.kind`.
#
# O `{}` literal NÃO é mass assignment: nele os campos estão escritos na
# própria chamada (por isso `_source` o marca como `"{}"` e a regra
# libera).
import ast
from pathlib import Path

from nucleus.rules.scanner.entity_binding import EntityBinding
from nucleus.rules.scanner.source_files import source_files


class MassAssignmentScanner:
    """
    Scanner responsável por identificar dados de ENTRADA que são
    despejados DIRETO em um contrato nomeado, sem passar por
    campos explícitos.

    Mass assignment acontece quando o corpo da requisição dita
    QUAIS campos do modelo serão preenchidos:

        DocumentEntity(**request.json)          ❌
        DocumentModel(**payload)                ❌
        DocumentEntity.from_dict(request.json)  ❌
        Model.query.update(**request.json)      ❌
        for key, value in payload.items():      ❌
            setattr(document, key, value)

    O caminho correto passa por campos explícitos:

        document = DocumentEntity(
            title=request.json["title"],        ✅
            owner_id=request.json["owner_id"],
        )

        document = DocumentEntity(
            **DocumentInput(**request.json)     ✅ (o Input filtra)
        )

    Por isso o scanner olha os nomes que terminam em `Input`,
    `Entity` e `Model`: são os contratos que NÃO podem ser
    preenchidos por um dicionário arbitrário.

    O scanner DESCREVE (o que veio, para onde vai e de que forma);
    quem decide a política é a Rule SOLAR-ARCH-029.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    # Contratos nomeados: quem recebe dados deve declarar os seus
    # próprios campos.
    #
    # Os três sufixos são as três famílias de contrato do projeto:
    # `Entity` (domínio), `Input` (entrada declarada) e `Model`
    # (mapeamento). `Service` e `UseCase` não entram — não são destino
    # de `**`, são quem CHAMA.
    BINDING_SUFFIXES = (
        "Entity",
        "Input",
        "Model",
    )

    # Métodos de escrita de ORM que aceitam o payload inteiro.
    #
    # A lista é por NOME, então cobre bibliotecas diferentes
    # (`Model.query.update(**x)`, `Model.create(**x)`): o critério é
    # "aceita **alguma coisa", e não "pertence ao SQLAlchemy".
    UPDATE_METHODS = frozenset({
        "create",
        "fill",
        "save",
        "update",
    })

    # Construtores alternativos que recebem um dicionário.
    #
    # Todos começam com `from_` porque é a convenção para "monte a
    # partir de": `from_dict`, `from_request`, `from_json`. O que muda
    # de um para o outro é só de ONDE vem o dado.
    MAPPING_METHODS = frozenset({
        "from_data",
        "from_dict",
        "from_form",
        "from_json",
        "from_payload",
        "from_request",
    })

    # Nome da função que escreve campo a campo. Usado para ACHAR a
    # chamada dentro do laço.
    SETTER = "setattr"

    # Os quatro valores possíveis de `EntityBinding.kind`. É o
    # vocabulário que a mensagem da regra usa para dizer de que forma o
    # preenchimento aconteceu.
    EXPANSION = "expansion"
    UPDATE = "update"
    MAPPING = "mapping"

    # Mesmo texto de `SETTER`, e de propósito: ali é o nome PROCURADO,
    # aqui é o VALOR do kind. Coincidem hoje, mas são coisas
    # diferentes — um é busca, o outro é vocabulário.
    SETATTR = "setattr"

    def __init__(self, root: Path):
        self.root = root.resolve()

    def scan(self) -> list[EntityBinding]:
        """
        Percorre o projeto e retorna os preenchimentos encontrados.
        """

        bindings: list[EntityBinding] = []

        for file in source_files(self.root):

            bindings.extend(
                self._scan_file(file)
            )

        return bindings

    def _scan_file(self, file: Path) -> list[EntityBinding]:
        """
        Analisa um único arquivo Python.
        """

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        relative = file.relative_to(self.root).as_posix()

        bindings: list[EntityBinding] = []

        # Duas formas de preencher em massa: a CHAMADA com `**`
        # (`DocumentEntity(**x)`) e o LAÇO que copia campo a campo com
        # `setattr` — que não tem `**` em lugar nenhum, mas faz o
        # mesmo.
        for node in ast.walk(tree):

            binding = None

            if isinstance(node, ast.Call):
                binding = self._call_binding(node, relative)

            elif isinstance(node, ast.For):
                binding = self._setattr_binding(node, relative)

            if binding is not None:
                bindings.append(binding)

        return bindings

    def _call_binding(
        self,
        node: ast.Call,
        file: str
    ) -> EntityBinding | None:
        """
        Descreve o preenchimento feito por uma chamada.
        """

        # Duas formas de chamada, testadas em ordem: o `from_dict(...)`
        # primeiro, e depois o `**` solto.
        mapping = self._mapping_binding(node, file)

        if mapping is not None:
            return mapping

        # `keyword.arg is None` é o `**`: keyword SEM NOME. Um
        # `title=...` tem `arg="title"` e NÃO é mass assignment — o
        # campo está declarado.
        expansions = [
            keyword.value
            for keyword in node.keywords
            if keyword.arg is None
        ]

        if not expansions:
            return None

        target, kind = self._receiver(node)

        # `kind is None` = quem recebe não é um contrato nomeado
        # (`dict.update(**x)`, por exemplo): não é mass assignment e não
        # vira achado.
        if kind is None:
            return None

        # `expansions[0]`: o PRIMEIRO `**`. Dois na mesma chamada é
        # raro, e o segundo não mudaria o diagnóstico.
        return EntityBinding(
            target=target,
            source=self._source(expansions[0]),
            kind=kind,
            file=file,
            line=node.lineno
        )

    def _receiver(
        self,
        node: ast.Call
    ) -> tuple[str, str | None]:
        """
        Devolve (quem recebe, de que forma) para uma chamada com
        expansão de dicionário.

        Duas formas são reconhecidas:

            DocumentEntity(**data)          → construtor do
                                              contrato;
            Model.query.update(**data)      → método de escrita.
        """

        name = self._receiver_name(node.func)

        # Último segmento = o MÉTODO chamado (`update`, `create`).
        leaf = name.split(".")[-1]

        # Caso 1: método de escrita de ORM. Quem recebe é o DONO
        # (`Model.query`, já sem o `.update`), porque é ele que a
        # mensagem cita.
        if leaf in self.UPDATE_METHODS:

            owner = name.rsplit(".", 1)[0] if "." in name else name

            if self._is_binding(owner):
                return owner, self.UPDATE

            return name, None

        # Caso 2: construtor do próprio contrato
        # (`DocumentEntity(**data)`).
        if self._is_binding(name):
            return name, self.EXPANSION

        # Recebedor que não é contrato nomeado.
        return name, None

    def _receiver_name(self, node: ast.AST) -> str:
        """
        Nome pontuado de quem recebe os dados, aceitando
        encadeamento:

            DocumentEntity(**x)                    → "DocumentEntity"
            Model.query.update(**x)                → "Model.query.update"
            Model.query.filter_by(id=1).update(**x) → o mesmo,
                                                      com o encadeamento
        """

        name = self._name(node)

        # `name or ast.unparse(node)`: `_name` devolve `""` quando a
        # base não é nome simples (encadeamento com chamada no meio —
        # `Model.query.filter_by(id=1).update(**x)`). Aí o texto do
        # `unparse` ainda diz o suficiente para a mensagem.
        return name or ast.unparse(node)

    def _mapping_binding(
        self,
        node: ast.Call,
        file: str
    ) -> EntityBinding | None:
        """
        Descreve `DocumentEntity.from_dict(request.json)`.
        """

        # `x.from_dict(...)` precisa ser ATRIBUTO — `from_dict` solto
        # não é a convenção de construtor de um contrato.
        if not isinstance(node.func, ast.Attribute):
            return None

        if node.func.attr not in self.MAPPING_METHODS:
            return None

        # Quem recebe é o objeto ANTES do ponto (`DocumentEntity`), e
        # ele precisa ser um contrato nomeado.
        owner = self._name(node.func.value)

        if not self._is_binding(owner):
            return None

        # Sem argumento não há de onde virem os dados.
        if not node.args:
            return None

        # Só o PRIMEIRO argumento: é ele que carrega o dicionário de
        # entrada na convenção `from_dict(dados, ...)`.
        return EntityBinding(
            target=owner,
            source=self._source(node.args[0]),
            kind=self.MAPPING,
            file=file,
            line=node.lineno
        )

    def _setattr_binding(
        self,
        node: ast.For,
        file: str
    ) -> EntityBinding | None:
        """
        Descreve o preenchimento campo a campo dentro de um laço.

            for key, value in payload.items():
                setattr(document, key, value)
        """

        # `walk` no LAÇO: o `setattr` pode estar dentro de um `if` ou de
        # um `try` no corpo do `for`.
        calls = [
            child
            for child in ast.walk(node)
            if isinstance(child, ast.Call)
            and self._name(child.func) == self.SETTER
        ]

        if not calls:
            return None

        # Só o PRIMEIRO `setattr`: um laço que escreve vários campos é o
        # mesmo achado, e o alvo do primeiro já o descreve.
        receiver = calls[0].args[0] if calls[0].args else None

        # `node.iter` é a ORIGEM: o que o `for` percorre
        # (`payload.items()`). É ele que a regra vai julgar.
        return EntityBinding(
            target=ast.unparse(receiver) if receiver else "<unknown>",
            source=self._source(node.iter),
            kind=self.SETATTR,
            file=file,
            line=calls[0].lineno
        )

    def _is_binding(self, name: str) -> bool:
        """
        Indica se o nome é de um contrato que declara os próprios
        campos (Entity / Input / Model).

        Olha o PRIMEIRO segmento, para pegar tanto
        `DocumentEntity` quanto `Model.query`.
        """

        # O PRIMEIRO segmento, e não o último: em `Model.query` quem
        # recebe é o `Model`, e o `query` é o que se faz com ele. Olhar o
        # último deixaria o `Model` de fora quando há encadeamento.
        first = name.split(".")[0]

        return first.endswith(self.BINDING_SUFFIXES)

    def _source(self, node: ast.AST) -> str:
        """
        Normaliza a origem dos dados.

            {…}                 → "{}"
            request.json        → "request.json"
            request.get_json()  → "request.get_json"
            DocumentInput(…)    → "DocumentInput"
            payload             → "payload"
        """

        # Dict literal → marcador `"{}"`. É o SINAL de "os campos estão
        # declarados aqui dentro", e é o que a SOLAR-ARCH-029 procura
        # para liberar.
        if isinstance(node, ast.Dict):
            return "{}"

        # Chamada → o NOME da função (`request.get_json`), porque os
        # parênteses e os argumentos não ajudam a mensagem.
        if isinstance(node, ast.Call):
            name = self._name(node.func)
            return name or ast.unparse(node)

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            return self._name(node)

        # Qualquer outra expressão: o texto dela, sem normalização.
        return ast.unparse(node)

    def _name(self, node: ast.AST) -> str:
        """
        Converte o alvo de uma chamada em nome pontuado.

        Devolve "" quando a base não é um nome simples — quem
        chama decide o que fazer com isso.
        """

        if isinstance(node, ast.Name):
            return node.id

        # RECURSIVO: cada `Attribute` pergunta pelo anterior, então
        # `Model.query.update` é montado de dentro para fora.
        if isinstance(node, ast.Attribute):

            base = self._name(node.value)

            # `if base else ""`: se algum ponto da cadeia não é nome
            # simples, a resposta inteira é vazia — melhor devolver nada
            # do que devolver um nome pela metade.
            return f"{base}.{node.attr}" if base else ""

        return ""
