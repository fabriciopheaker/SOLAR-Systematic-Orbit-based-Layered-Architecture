# O Blueprint que DECLARA os guardas na própria rota.
#
# O `add_url_rule` do Flask não conhece `sanitizer=` nem `validator=`:
# os keywords dele são os do `Rule` do Werkzeug, e qualquer outro
# estoura `TypeError`. Este Blueprint existe para que a ROTA declare
# quem protege a entrada dela — que é onde quem lê o arquivo de rotas
# procura a informação.
#
# O que ele acrescenta é UMA coisa: guardar o par (Sanitizer,
# Validator) de cada endpoint e entregá-lo ao mecanismo da Atmosphere
# (`apply`), que roda no `before_request`. Nenhum Controller conhece
# Sanitizer, Validator ou RequestPipeline.
from flask import Blueprint

from nucleus.middleware.atmosphere import apply


class SolarBlueprint(Blueprint):
    """
    Blueprint que aceita `sanitizer=` e `validator=` na rota.

        blueprint = SolarBlueprint(
            "example",
            __name__,
            url_prefix="/examples"
        )

        blueprint.add_url_rule(
            "/users",
            "create_example_user",
            CreateUserController.create,
            methods=["POST"],
            sanitizer=CreateUserSanitizer,
            validator=CreateUserValidator,
        )

    A rota declara os dois, e o pipeline roda ANTES do Controller:
    quando ele for chamado, o corpo já está tratado.

    Rota SEM os keywords passa direto: é entrada que não transporta
    dados (um GET, por exemplo), e não há o que limpar nem o que
    exigir.
    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # ENDPOINT → (Sanitizer, Validator), preenchido pelas rotas
        # deste Blueprint.
        #
        # O mapa é entregue ao `apply` por REFERÊNCIA e lido a cada
        # requisição: por isso a ordem entre registrar a rota e o
        # `before_request` não importa.
        self._guards: dict = {}

        self.before_request(apply(self._guards))

    def add_url_rule(
        self,
        rule,
        endpoint=None,
        view_func=None,
        provide_automatic_options=None,
        *,
        sanitizer=None,
        validator=None,
        **options
    ):
        """
        Registra a rota e guarda os guardas declarados nela.
        """

        # Só entra no mapa a rota que DECLAROU guarda. Rota sem
        # keyword nenhum não vira par de `None` no mapa: ausência de
        # guarda é ausência — e é a SOLAR-ARCH-013 que decide se
        # aquela entrada precisava de uma.
        if sanitizer is not None or validator is not None:

            self._guards[
                self._endpoint_of(endpoint, view_func)
            ] = (
                _as_guard(sanitizer),
                _as_guard(validator),
            )

        super().add_url_rule(
            rule,
            endpoint,
            view_func,
            provide_automatic_options,
            **options
        )

    @staticmethod
    def _endpoint_of(endpoint, view_func) -> str:
        """
        O endpoint da rota.

        O Flask aceita `endpoint=None` e deriva o nome da função de
        visão. É o MESMO nome que o `local_endpoint()` do mecanismo da
        Atmosphere vai ler em `request.endpoint`.
        """

        if endpoint is not None:
            return endpoint

        return view_func.__name__


def _as_guard(guard):
    """
    O guarda pronto para o pipeline.

    Aceita a CLASSE (`CreateUserSanitizer`) ou a INSTÂNCIA
    (`CreateUserSanitizer()`): quem declara a rota não precisa
    instanciar, e a instância é criada UMA vez aqui.

    O pipeline exige instância — é ela que carrega a configuração
    (campos obrigatórios, limites) —, e criá-la por requisição
    montaria o guarda de novo a cada chamada sem que nada mude.
    """

    if isinstance(guard, type):
        return guard()

    return guard
