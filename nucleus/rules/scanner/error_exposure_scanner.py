# Scanner de VAZAMENTO de detalhe interno em erro (SOLAR-SEG-008).
#
# Três decisões estruturam o arquivo, e cada uma está explicada no lugar
# onde acontece:
#
#   1. o que CONTA como detalhe — `_detail`;
#   2. qual detalhe vale quando um está dentro do outro — `_outermost`;
#   3. para ONDE o detalhe vai — `_destination`, que procura em duas
#      direções e só acusa quando o detalhe VIAJA no valor de saída.
#
# O item 3 é o que evita falso positivo: passar perto de um `return` não
# basta — o detalhe tem que estar DENTRO do que sai.
import ast
from collections.abc import Iterator
from pathlib import Path

from nucleus.rules.scanner.error_exposure import ErrorExposure
from nucleus.rules.scanner.source_files import source_files


class ErrorExposureScanner:
    """
    Scanner responsável por identificar DETALHES INTERNOS de erro
    sendo usados dentro de um `except`.

    O que interessa NÃO é usar a exceção: é MANDÁ-LA para fora.

    VAZAMENTO (o detalhe volta para quem chamou):

        except Exception as error:
            return {"error": str(error)}            ❌
            return jsonify({"erro": f"{error}"})    ❌
            raise ValueError(f"falhou: {error}")    ❌
            return {"traceback": traceback.format_exc()}  ❌

    CORRETO (o detalhe fica no log do servidor):

        except Exception as error:
            logger.exception("falha ao processar")
            return {"error": "não foi possível processar"}  ✅

    NÃO ACUSADO (não foi possível provar que o detalhe sai):

        except SolarException as error:
            violacoes.append(Violacao(mensagem=str(error)))  ✅

    Detalhes reconhecidos: str(), repr(), "{}".format(),
    f-string, .args, .__traceback__, format_exc() e exc_info().

    O scanner DESCREVE o DESTINO do detalhe — `response` quando
    demonstravelmente sai do handler, `log` quando vai para o log,
    `local` quando não se pode provar que sai. Quem decide a
    política é a Rule SOLAR-SEG-008.

    O código NÃO é executado: a análise é feita sobre a AST.
    """

    # Chamadas que RENDERIZAM a exceção.
    #
    # É um mapa, e não um conjunto, porque o rótulo pode ser diferente
    # do nome da função — `str` e `repr` são formas de detalhe distintas
    # na mensagem.
    DETAIL_CALLS = {
        "str": "str",
        "repr": "repr",
    }

    # Atributos que CARREGAM o interior da exceção.
    #
    # `__traceback__` ganha o rótulo "traceback" porque é isso que ele
    # é: o rastro inteiro, e não só a mensagem.
    DETAIL_ATTRIBUTES = {
        "args": "args",
        "__traceback__": "traceback",
    }

    # Chamadas que devolvem o traceback inteiro. São reconhecidas
    # pelo ÚLTIMO segmento: cobre `traceback.format_exc()` e o
    # `format_exc()` importado direto.
    #
    # É o único detalhe que NÃO menciona a variável da exceção — daí ser
    # testado ANTES de `_mentions` em `_detail`.
    TRACEBACK_FUNCTIONS = frozenset({
        "exc_info",
        "format_exc",
        "format_exception",
        "print_exc",
        "print_exception",
    })

    # Métodos de LOG: o detalhe vai para o servidor, não para o
    # cliente — é o destino CORRETO, e `_destination` o reconhece para
    # não acusar quem faz certo.
    #
    # O vocabulário é o do `logging`, e vale para `logger.error`,
    # `log.exception` e qualquer objeto — o teste é pelo último nome.
    LOGGING_METHODS = frozenset({
        "critical",
        "debug",
        "error",
        "exception",
        "info",
        "log",
        "warn",
        "warning",
    })

    # Montadores de RESPOSTA: o detalhe está voltando para quem
    # chamou.
    #
    # Não são só o `return`: `jsonify(...)` MONTA a resposta e
    # `abort(...)` levanta o erro HTTP — nos dois o detalhe sai da
    # aplicação.
    RESPONSE_BUILDERS = frozenset({
        "HttpResponse",
        "JSONResponse",
        "Response",
        "abort",
        "dumps",
        "jsonify",
        "make_response",
    })

    # Os três destinos possíveis. Só `response` é acusado pela regra;
    # `local` existe para não tratar como vazamento aquilo que o scanner
    # não conseguiu provar.
    RESPONSE = "response"
    LOG = "log"
    LOCAL = "local"

    def __init__(self, root: Path):
        self.root = root.resolve()

    def scan(self) -> list[ErrorExposure]:
        """
        Percorre o projeto e retorna os usos encontrados.
        """

        exposures: list[ErrorExposure] = []

        for file in source_files(self.root):

            exposures.extend(
                self._scan_file(file)
            )

        return exposures

    def _scan_file(self, file: Path) -> list[ErrorExposure]:
        """
        Analisa um único arquivo Python.

        O código NÃO é executado: a análise é feita sobre a AST.
        """

        tree = ast.parse(
            file.read_text(encoding="utf-8"),
            filename=str(file)
        )

        relative = file.relative_to(self.root).as_posix()
        parents = _parent_map(tree)

        exposures: list[ErrorExposure] = []

        # Só handler de exceção: é o único lugar onde "a exceção" existe
        # como variável.
        for node in ast.walk(tree):

            if not isinstance(node, ast.ExceptHandler):
                continue

            # `except Exception:` sem `as nome` não tem variável — não há
            # detalhe para vazar por um nome.
            if node.name is None:
                continue

            exposures.extend(
                self._handler_exposures(
                    node,
                    relative,
                    parents
                )
            )

        return exposures

    def _handler_exposures(
        self,
        handler: ast.ExceptHandler,
        file: str,
        parents: dict[ast.AST, ast.AST]
    ) -> list[ErrorExposure]:
        """
        Descreve os detalhes internos usados em um handler.
        """

        name = handler.name

        # Varre o HANDLER, e não o arquivo: o detalhe só interessa dentro
        # do bloco que trata a exceção. Cada nó vira um par
        # (nó, rótulo do detalhe), e o que não é detalhe cai fora.
        found = [
            (node, detail)
            for node, detail in (
                (node, self._detail(node, name))
                for node in ast.walk(handler)
            )
            if detail is not None
        ]

        # Antes de julgar o destino, tira o detalhe que está DENTRO de
        # outro detalhe — ver `_outermost`.
        outermost = self._outermost(found, parents)

        return [
            ErrorExposure(
                handler=name,
                detail=detail,
                destination=self._destination(
                    node,
                    parents,
                    handler
                ),
                file=file,
                line=node.lineno
            )
            for node, detail in outermost
        ]

    def _outermost(
        self,
        found: list[tuple[ast.AST, str]],
        parents: dict[ast.AST, ast.AST]
    ) -> list[tuple[ast.AST, str]]:
        """
        Descarta os detalhes que estão DENTRO de outro detalhe.

        `f"{str(error)}"` casaria duas vezes; o que vale é o
        de fora.
        """

        # Conjunto para a busca dentro do `any` abaixo ser O(1).
        nodes = {node for node, _ in found}

        # O nó fica se NENHUM dos seus ancestrais também é detalhe; o
        # `any` sobre os ancestrais é o que descarta o de dentro.
        return [
            (node, detail)
            for node, detail in found
            if not any(
                ancestor in nodes
                for ancestor in _ancestors(node, parents)
            )
        ]

    def _detail(self, node: ast.AST, name: str) -> str | None:
        """
        Devolve o rótulo do detalhe interno, ou None.
        """

        # O traceback é o PRIMEIRO teste porque é o único caso que NÃO
        # menciona a variável da exceção: `format_exc()` lê o rastro de
        # `sys.exc_info()`, e o retorno dele já é o detalhe.
        if isinstance(node, ast.Call):

            last = self._name(node.func).split(".")[-1]

            if last in self.TRACEBACK_FUNCTIONS:
                return "traceback"

        # Fora isso, o nó só interessa se falar DAQUELA exceção.
        if not self._mentions(node, name):
            return None

        # `error.args` / `error.__traceback__`.
        if isinstance(node, ast.Attribute):
            return self.DETAIL_ATTRIBUTES.get(node.attr)

        # A f-string é interpolação: se ela menciona a exceção, o valor
        # dela está sendo montado dentro do texto.
        if isinstance(node, ast.JoinedStr):
            return "f-string"

        # `str(error)`, `repr(error)` e `"{}".format(error)`.
        if isinstance(node, ast.Call):

            last = self._name(node.func).split(".")[-1]

            if last == "format":
                return "format"

            return self.DETAIL_CALLS.get(last)

        return None

    def _destination(
        self,
        node: ast.AST,
        parents: dict[ast.AST, ast.AST],
        handler: ast.ExceptHandler
    ) -> str:
        """
        Diz para onde o detalhe vai.

        Procura em DUAS direções, porque o detalhe pode sair de
        duas formas:

            1. dentro da própria expressão que sai
               (`return {"error": str(error)}`);
            2. guardado em uma variável e usado em OUTRA instrução
               (`detalhe = str(error)` … `return {"e": detalhe}`)
               — a atribuição e o `return` são irmãos, e subir a
               árvore a partir do detalhe nunca chega lá.

        Em cada ponto de saída verifica se o detalhe REALMENTE
        viaja nele:

            log      uma chamada de log (o detalhe fica no
                     servidor);
            response return, raise ou montador de resposta que
                     CONTÉM o detalhe;
            local    nenhum dos dois — não foi possível provar que
                     o detalhe sai do handler.

        A verificação de CONTEÚDO é o que evita falso positivo.
        Passar por um `return` não basta: sem isso,
        `violacoes.append(Violacao(mensagem=str(error)))` seria
        acusado só porque existe um `return` acima — quando o
        detalhe virou registro, não resposta.
        """

        # Primeiro os nomes que receberam o detalhe e NÃO foram
        # reaproveitados — são eles que permitem achar o detalhe em
        # outra instrução (ver `_traceable_names`).
        names = self._traceable_names(node, parents, handler)

        # PRIMEIRA direção: subir a árvore. Aqui se pega o detalhe que
        # sai na própria expressão em que aparece.
        for ancestor in _ancestors(node, parents):

            # `raise` e `return` só acusam se o detalhe ESTIVER no valor
            # que sai — é esta checagem de conteúdo que evita o falso
            # positivo.
            if isinstance(ancestor, ast.Raise):

                if self._carries(ancestor.exc, node, names):
                    return self.RESPONSE

                continue

            if isinstance(ancestor, ast.Return):

                if self._carries(ancestor.value, node, names):
                    return self.RESPONSE

                continue

            if not isinstance(ancestor, ast.Call):
                continue

            last = self._name(ancestor.func).split(".")[-1]

            # Chamada de log vence: o detalhe está no servidor, que é o
            # destino CORRETO e o que a SOLAR-SEG-008 recomenda.
            if last in self.LOGGING_METHODS:
                return self.LOG

            if last in self.RESPONSE_BUILDERS:
                return self.RESPONSE

        # SEGUNDA direção: o detalhe pode ter sido guardado em uma
        # variável e sair em OUTRA instrução. `detalhe = str(error)` e
        # `return {"error": detalhe}` são irmãos, então subir a árvore
        # nunca chega até o `return`.
        if self._escapes_through(names, handler):
            return self.RESPONSE

        # Não foi possível provar que sai. `local` é resposta diferente
        # de `response` — e a regra NÃO acusa `local`.
        return self.LOCAL

    def _traceable_names(
        self,
        node: ast.AST,
        parents: dict[ast.AST, ast.AST],
        handler: ast.ExceptHandler
    ) -> frozenset[str]:
        """
        Nomes que recebem o detalhe e NÃO são reaproveitados.

        Um nível só — `detalhe = str(error)`. A exigência de
        atribuição ÚNICA evita acusar um nome que depois recebe uma
        mensagem genérica:

            detalhe = str(error)
            logger.error(detalhe)
            detalhe = "não foi possível processar"
            return {"error": detalhe}          ← não é vazamento
        """

        # O `== 1` é a exigência de atribuição ÚNICA: um nome
        # reaproveitado depois pode estar carregando outra coisa, e
        # segui-lo acusaria o inocente (ver o exemplo no docstring).
        return frozenset(
            name
            for name in self._assigned_names(node, parents)
            if self._assignments(handler, name) == 1
        )

    def _assignments(
        self,
        handler: ast.ExceptHandler,
        name: str
    ) -> int:
        """
        Quantas vezes o nome é atribuído no handler.
        """

        count = 0

        # Duas formas de atribuir: `x = ...` (lista de alvos, por causa
        # de `a = b = ...`) e `x: T = ...` (alvo único). Qualquer outro
        # nó não atribui nada.
        for child in ast.walk(handler):

            if isinstance(child, ast.Assign):
                targets = child.targets

            elif isinstance(child, ast.AnnAssign):
                targets = [child.target]

            else:
                continue

            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in targets
            ):
                count += 1

        return count

    def _escapes_through(
        self,
        names: frozenset[str],
        handler: ast.ExceptHandler
    ) -> bool:
        """
        Indica se algum ponto de saída do handler leva um dos nomes.
        """

        # Sem nome rastreável não há como achar o detalhe em outra
        # instrução — e varrer o handler seria trabalho perdido.
        if not names:
            return False

        for child in ast.walk(handler):

            escaping = self._escaped_value(child)

            if escaping is not None and self._carries(
                escaping,
                None,
                names
            ):
                return True

        return False

    def _escaped_value(self, node: ast.AST) -> ast.AST | None:
        """
        O valor que SAI do handler neste nó, ou None.

            return X        → X
            raise X         → X
            jsonify(X)      → X (montador de resposta)
        """

        if isinstance(node, ast.Return):
            return node.value

        if isinstance(node, ast.Raise):
            return node.exc

        # Montador de resposta devolve a PRÓPRIA chamada: `jsonify(X)`
        # já é a resposta, e `X` está dentro dela.
        if isinstance(node, ast.Call):

            last = self._name(node.func).split(".")[-1]

            if last in self.RESPONSE_BUILDERS:
                return node

        # Nó que não é ponto de saída.
        return None

    def _assigned_names(
        self,
        node: ast.AST,
        parents: dict[ast.AST, ast.AST]
    ) -> frozenset[str]:
        """
        Nomes que recebem o detalhe DIRETAMENTE.

            detalhe = str(error)      → {"detalhe"}
        """

        # É o PAI que diz se o detalhe está sendo atribuído: o nó do
        # detalhe é o LADO DIREITO, e é a instrução de cima que tem o
        # alvo.
        parent = parents.get(node)

        if isinstance(parent, ast.Assign):

            # `if isinstance(target, ast.Name)`: alvo de atributo
            # (`self.detalhe = ...`) fica de fora — nome de atributo é
            # rastreável demais para uma busca por nome simples.
            return frozenset(
                target.id
                for target in parent.targets
                if isinstance(target, ast.Name)
            )

        if (
            isinstance(parent, ast.AnnAssign)
            and isinstance(parent.target, ast.Name)
        ):
            return frozenset({parent.target.id})

        # Não está sendo atribuído a nada (uso direto na expressão).
        return frozenset()

    def _carries(
        self,
        expression: ast.AST | None,
        node: ast.AST | None,
        names: frozenset[str]
    ) -> bool:
        """
        Indica se a expressão LEVA o detalhe para fora.

        Leva quando contém o próprio detalhe ou quando usa um dos
        nomes que o receberam.
        """

        # `return` sem valor, por exemplo: não há o que levar.
        if expression is None:
            return False

        # Duas formas de o detalhe estar na expressão: o PRÓPRIO nó
        # (`node is child`, identidade) ou um dos nomes que o receberam.
        return any(
            (node is not None and child is node)
            or (isinstance(child, ast.Name) and child.id in names)
            for child in ast.walk(expression)
        )

    def _mentions(self, node: ast.AST, name: str) -> bool:
        """
        Indica se a expressão menciona a variável da exceção.
        """

        # Comparação por NOME e não por identidade: em
        # `except Exception as error`, o `error` do `str(error)` é um nó
        # DIFERENTE do nome que o handler declara.
        return any(
            isinstance(child, ast.Name) and child.id == name
            for child in ast.walk(node)
        )

    def _name(self, node: ast.AST) -> str:
        """
        Converte o alvo de uma chamada em nome pontuado.

            jsonify                → "jsonify"
            traceback.format_exc   → "traceback.format_exc"
            "...".format           → "format"
        """

        if isinstance(node, ast.Name):
            return node.id

        # RECURSIVO: `traceback.format_exc` é montado de dentro para
        # fora.
        if isinstance(node, ast.Attribute):

            base = self._name(node.value)

            # AQUI o fallback é `node.attr`, e não `""` como no scanner
            # de mass assignment: o alvo pode ser um LITERAL
            # (`"...".format`), e nesse caso o único nome útil é o
            # atributo.
            return f"{base}.{node.attr}" if base else node.attr

        return ""


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    """
    Mapeia cada nó da AST para o seu pai.
    """

    parents: dict[ast.AST, ast.AST] = {}

    # Percorre os PAIS para gravar a volta (`filho -> pai`).
    for parent in ast.walk(tree):

        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    return parents


def _ancestors(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST]
) -> Iterator[ast.AST]:
    """
    Percorre os ancestrais do nó, do mais próximo ao mais distante.
    """

    current = node

    # `while current in parents` é a condição de parada: a RAIZ não tem
    # pai. O `yield` sobe um nível por vez, do mais próximo ao mais
    # distante.
    while current in parents:

        current = parents[current]

        yield current
