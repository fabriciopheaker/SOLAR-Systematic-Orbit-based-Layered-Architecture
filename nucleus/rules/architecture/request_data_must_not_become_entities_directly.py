# SOLAR-SEG-009 — mass assignment.
#
# O que a regra persegue é o CLIENTE escolhendo quais campos do modelo
# são escritos (`is_admin`, `owner_id`). Por isso o critério é "os
# campos estão declarados?", e não "veio da requisição?" — ver
# `_is_explicit`.
from nucleus.exceptions.solar_exception import SolarException
from nucleus.rules.rule import SECURITY, Rule, rule_code
from nucleus.rules.scanner.entity_binding import EntityBinding


class RequestDataMustNotBecomeEntitiesDirectly(Rule):
    """
    Regra arquitetural:

    SOLAR-SEG-009

    Dados arbitrários da requisição NÃO podem ser transformados
    diretamente em Entity/Model (mass assignment).

    Quando o corpo da requisição dita QUAIS campos do modelo são
    preenchidos, quem chama escolhe o que escrever no banco —
    inclusive campos que a API nunca pretendeu expor:

        # requisição maliciosa
        POST /documents
        {"title": "ok", "owner_id": 99, "is_admin": true}

        DocumentEntity(**request.json)      ❌ vira admin

    É VIOLAÇÃO:

        DocumentEntity(**request.json)          ❌
        DocumentModel(**payload)                ❌
        Model.query.update(**request.json)      ❌
        DocumentEntity.from_dict(request.json)  ❌
        for key, value in payload.items():      ❌
            setattr(document, key, value)

    Correto — o conjunto de campos é DECLARADO, não escolhido pelo
    cliente:

        document = DocumentEntity(
            title=request.json["title"],        ✅
            owner_id=request.json["owner_id"],
        )

        document = DocumentEntity(
            **DocumentInput(**request.json)     ✅ (o Input filtra)
        )

        document = DocumentEntity(**{           ✅ (campos explícitos)
            "title": request.json["title"],
            "owner_id": request.json["owner_id"],
        })

    A regra conversa com a SOLAR-ROF-003 na fronteira: o `Input` é
    o contrato que DECLARA os campos aceitos. Um dicionário
    literal também é aceito, porque nele os campos estão à vista.

    Para `setattr` em laço o critério é mais estreito — o alvo não
    é conhecido estaticamente —, então só é violação quando a
    origem dos dados é declaradamente da requisição
    (REQUEST_NAMES).

    Documentado como limitação: o scanner pega o que está escrito
    na chamada; dados que passam por várias funções antes de
    chegar ao modelo não são rastreáveis estaticamente.

    O contexto desta regra é um EntityBinding.
    """

    # Origem EXPLÍCITA: os campos estão declarados.
    LITERAL_SOURCE = "{}"
    EXPLICIT_SUFFIXES = ("Input",)

    # Vocabulário de origem de dados de REQUISIÇÃO, usado só para
    # o caso de `setattr` em laço.
    REQUEST_NAMES = frozenset({
        "args",
        "body",
        "data",
        "dados",
        "filters",
        "form",
        "json",
        "params",
        "payload",
        "query",
        "request",
        "values",
    })

    LOOP_KIND = "setattr"

    def code(self) -> str:
        return rule_code(SECURITY, 9)

    def description(self) -> str:
        return (
            "Dados arbitrários da requisição não podem ser "
            "transformados diretamente em Entity/Model."
        )

    def validate(self, binding: EntityBinding) -> None:

        # Uma única pergunta, com o caso do laço tratado DENTRO dela: o
        # `setattr` tem critério mais estreito porque o alvo não é
        # conhecido estaticamente.
        if not self._is_violation(binding):
            return

        raise SolarException(
            self._build_message(binding)
        )

    def _is_violation(self, binding: EntityBinding) -> bool:

        # No laço o alvo é DESCONHECIDO, então exigimos TAMBÉM que a
        # origem se declare da requisição. Sem esse cuidado, copiar
        # campo a campo de um objeto de domínio seria acusado.
        if binding.kind == self.LOOP_KIND:

            return (
                self._mentions_request(binding.source)
                and not self._is_explicit(binding.source)
            )

        # Nos demais casos basta a origem não ser explícita: se os
        # campos não estão à vista, quem escolheu foi o cliente.
        return not self._is_explicit(binding.source)

    def _is_explicit(self, source: str) -> bool:
        """
        Indica se os campos preenchidos estão DECLARADOS.

        Vale um dicionário literal (campos à vista) e um contrato
        nomeado de entrada (`...Input`).
        """

        # Dicionário literal: os campos estão ESCRITOS na chamada.
        if source == self.LITERAL_SOURCE:
            return True

        # Contrato nomeado de entrada (`DocumentInput`): o Input é quem
        # declara os campos aceitos — é a solução que a SOLAR-ROF-003
        # também empurra.
        return any(
            segment.endswith(self.EXPLICIT_SUFFIXES)
            for segment in source.split(".")
        )

    def _mentions_request(self, source: str) -> bool:

        # Por SEGMENTO e em minúsculas: `request.json` e
        # `Request.Form` são a mesma origem. Um nome solto que não está
        # no vocabulário não conta — é o que evita acusar laço sobre
        # dado interno.
        return any(
            segment.lower() in self.REQUEST_NAMES
            for segment in source.split(".")
        )

    def _build_message(self, binding: EntityBinding) -> str:

        return (
            f"{self.code()}: dados de '{binding.source}' preenchem "
            f"'{binding.target}' como um todo ({binding.kind}) em "
            f"{binding.file}:{binding.line}. "
            f"Declare os campos aceitos — explicitamente ou por um "
            f"contrato de entrada (...Input): o cliente não escolhe "
            f"quais campos do modelo serão escritos."
        )
