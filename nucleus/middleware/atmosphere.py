# Mecanismo da FRONTEIRA do Planet.
#
# Quem DECLARA os guardas de entrada é a ROTA (`sanitizer=` e
# `validator=`, no `add_url_rule`); quem os APLICA é este mecanismo,
# ligado ao Blueprint do Planet por `before_request` — ver
# `SolarBlueprint`, que monta o mapa que este módulo consome.
#
# É um `before_request` de verdade, e não um pipeline inventado: os
# guardas rodam ANTES de qualquer Controller daquele Planet, e o
# Controller recebe a requisição já tratada. Nenhum Controller
# conhece Sanitizer, Validator ou RequestPipeline.
from flask import g, request

from nucleus.contracts.http_input import HttpInput
from nucleus.middleware.request_pipeline import RequestPipeline


# Onde o corpo tratado espera até o Controller pedir.
#
# Fica no `g` do Flask, que é o contexto da REQUISIÇÃO: duas
# requisições simultâneas não se enxergam, o que um atributo de
# módulo não garantiria.
#
# O VALOR é o nome que o Controller escreve — `g.solar_data`. Está
# aqui para haver um lugar só que decide a chave, e o Controller a
# cita direto, sem import nenhum entre a fronteira e ele.
TREATED_DATA = "solar_data"

# Uma instância só, criada na importação.
#
# O pipeline não guarda estado entre requisições, e recriá-lo a cada
# chamada montaria um `RuleEngine` por requisição — trabalho que não
# muda nada no resultado.
_PIPELINE = RequestPipeline()


def apply(entries):
    """
    Devolve a função de fronteira do Planet.

    `entries` mapeia ENDPOINT → (Sanitizer, Validator). Quem o monta é
    o `SolarBlueprint`, a partir dos guardas que cada ROTA declarou:

        # planets/example/routes.py
        blueprint = SolarBlueprint("example", __name__, ...)

        blueprint.add_url_rule(
            "/users",
            "create_example_user",
            CreateUserController.create,
            methods=["POST"],
            sanitizer=CreateUserSanitizer,
            validator=CreateUserValidator,
        )

    O que o mecanismo liga é o resultado:

        self.before_request(apply(self._guards))

    Endpoint que NÃO está no mapa passa direto: é rota que não
    transporta dados (um GET, por exemplo), e não há o que validar
    nem o que limpar.
    """

    def protect():

        # SEMPRE presente, mesmo quando a rota não tem guarda
        # declarado: o Controller lê `g.solar_data` sem se preocupar,
        # e rota fora do mapa recebe vazio em vez de um
        # `AttributeError` que apareceria longe da causa.
        setattr(g, TREATED_DATA, {})

        guards = entries.get(local_endpoint())

        if guards is None:
            return None

        sanitizer, validator = guards

        # `silent=True`: corpo ausente ou malformado vira `None`, e
        # quem recusa é o Validator — com código e mensagem de
        # contrato, em vez de a biblioteca estourar antes, com erro
        # dela.
        payload = request.get_json(silent=True)

        # `carries_data=True` explícito: estar no mapa JÁ É declarar
        # que esta entrada transporta dados. Por isso o `content_type`
        # não aparece em nenhum lugar — JSON é o normal, e o caso
        # especial (upload, form) tem guarda próprio no mapa.
        http_input = HttpInput(
            method=request.method,
            name=request.path,
            sanitizer=sanitizer,
            validator=validator,
            carries_data=True,
        )

        # A ordem (validar → sanitizar) é do RequestPipeline, e é o
        # motivo de ele existir: um lugar só decide isso.
        setattr(
            g,
            TREATED_DATA,
            _PIPELINE.handle(http_input, payload)
        )

        return None

    return protect


def local_endpoint() -> str:
    """
    O endpoint da rota SEM o prefixo do Blueprint.

    Registrado num Blueprint, o Flask prefixa o endpoint com o nome
    dele — a rota de `/examples/users` vira
    `example.create_example_user`. O mapa da Atmosphere usa o nome
    LOCAL (o que está escrito no `add_url_rule`), porque é o nome que
    o Planet escreveu e conhece.

    Um Blueprint aninhado (`orbits.example.create_example_user`)
    também funciona: o nome local é sempre o ÚLTIMO segmento.
    """

    endpoint = request.endpoint or ""

    return endpoint.rsplit(".", 1)[-1]
