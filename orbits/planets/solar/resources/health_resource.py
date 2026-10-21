# Resource da rota de saúde: o exemplo vivo do fluxo
# Controller -> Resource -> Response.
from nucleus.contracts.resource import Resource


class HealthResource(Resource):
    """
    Resource da verificação de saúde da aplicação.

    É a ÚLTIMA etapa antes de a resposta sair: o que o cliente
    recebe é o que `to_object` devolve.
    """

    @classmethod
    def to_object(cls, data) -> dict:
        """
        Representação da resposta da verificação.

        `data` é o que o Controller entregou. Hoje vem vazio; o `get`
        com valor padrão deixa o Resource pronto para quando não
        vier.
        """

        # Só o que o cliente precisa ver.
        #
        # `(data or {})` e não `data`: o Resource aceita ser chamado
        # sem dado, e a verificação de saúde não pode quebrar por
        # causa de um campo que não é assunto dela.
        #
        # `message` é fixo: quem abre a rota no navegador precisa ver
        # uma resposta legível, e "bem-vindo" é o recado de que a
        # aplicação está de pé.
        return {
            "status": "ok",
            "message": "bem-vindo",
            "application": (data or {}).get("application", ""),
        }
