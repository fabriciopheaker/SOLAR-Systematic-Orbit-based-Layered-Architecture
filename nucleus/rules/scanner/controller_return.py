# Contexto da SOLAR-ARCH-014: o RETORNO de um método de Controller.
#
# O contexto vem do `ControllerReturnScanner`, que lê o `return` dos
# métodos públicos de cada Controller. O scanner descreve o FATO; a
# regra decide a POLÍTICA.
from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerReturn:
    """
    Descreve o retorno de um MÉTODO de Controller.

        controller = "CreateUserController"
        method     = "create"
        resources  = {"UserResource(output)"}

    controller:
        Nome da classe Controller.

    method:
        Nome do método. Só os PÚBLICOS entram: `__init__` e os
        auxiliares privados não são rota, e acusá-los seria acusar
        código que não responde requisição nenhuma.

    resources:
        Os nomes em que o Resource foi chamado no retorno — a forma
        concreta de "a resposta passou por um Resource".

        Conjunto VAZIO significa que o retorno não passou por
        Resource nenhum. É isso que a SOLAR-ARCH-014 acusa.

    file / line:
        Onde o método foi declarado.
    """

    controller: str
    method: str
    resources: frozenset[str]
    file: str
    line: int

    def uses_resource(self) -> bool:
        """
        Resposta resolvida: o retorno passou por um Resource?

        O critério é a chamada a `render` no próprio retorno: quem
        monta a representação da resposta é o Resource, e chamá-lo é
        o que tira do Controller a decisão do que sai.
        """

        return bool(self.resources)
