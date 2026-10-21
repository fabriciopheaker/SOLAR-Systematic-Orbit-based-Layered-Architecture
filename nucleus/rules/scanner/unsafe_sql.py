# Contexto da SOLAR-SEG-011: construção de SQL por interpolação.
#
# O achado é sempre uma INTERPOLAÇÃO — o valor dinâmico entra na
# string. SQL montado só com pedaços literais não é perigoso e não
# chega aqui, mesmo que seja feio.
from dataclasses import dataclass


@dataclass(frozen=True)
class UnsafeSql:
    """
    Representa uma CONSTRUÇÃO INSEGURA de SQL encontrada no
    código-fonte.

    O scanner só produz esta estrutura quando há INTERPOLAÇÃO de
    valores dinâmicos — que é o que abre espaço para injeção:

        "SELECT * FROM users WHERE id = " + user_id      ❌
        f"SELECT * FROM users WHERE id = {user_id}"      ❌
        "SELECT ... %s" % user_id                        ❌
        "SELECT ... {}".format(user_id)                  ❌

    NÃO é construída insegura:

        "SELECT * FROM users WHERE id = :id"             ✅
        "SELECT * FROM users " + "WHERE id = :id"        ✅ (estático)

    module:
        Módulo onde a construção foi encontrada.

    kind:
        Forma da construção:
            concatenation / f-string / percent / format

    file / line:
        Onde a construção aparece.
    """

    module: str

    # A forma da construção (concatenation / f-string / percent /
    # format). Todas são inseguras, mas a mensagem diz qual foi: é o
    # que permite a quem corrige escolher a troca certa por
    # parâmetro vinculado.
    kind: str

    file: str
    line: int
