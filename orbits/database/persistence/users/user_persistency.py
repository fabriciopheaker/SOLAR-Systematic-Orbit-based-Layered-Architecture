"""Operações de persistência dos usuários.

É a camada que sabe COMO ler e gravar usuário: monta o Model,
consulta e confirma a transação. O Repository do Planet fala com
ela — e ninguém acima do Repository vê o Model.

A sessão vem da fachada `Database`, e não de um `import sqlalchemy`:
só o driver conhece a tecnologia (SOLAR-ARCH-010).
"""


def _users_model():
    """
    O Model dos usuários, importado NA CHAMADA.

    O import não pode ficar no topo do módulo, e a razão é de ORDEM:
    `class Users(Database.orm)` precisa da ORM JÁ PUBLICADA pelo
    driver, e este módulo é alcançado a partir do `kernel.py` — que
    importa `orbits.routes` no topo, antes de `mount()` rodar o
    `Database.init()`.

    Aqui dentro é seguro: quando um método desta classe roda, a
    montagem já aconteceu e o módulo do Model já está em
    `sys.modules` — o import custa uma consulta a dicionário.
    """

    from orbits.database.models.user_model import Users

    return Users


class UserPersistency:
    """
    Operações de persistência dos usuários.

    Quem monta o Model é ESTA camada — e é por isso que o Planet não
    precisa conhecê-lo: o Repository fala com o `Persistence`, e o
    que sobe de volta são dados.
    """

    def __init__(self, database):
        # A fachada, recebida de cima. A sessão é pedida a ela a cada
        # operação, e não guardada aqui: sessão guardada em atributo
        # sobrevive a um `close()` e vira erro obscuro depois.
        self.database = database

    def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str
    ):
        """
        Grava o usuário e devolve o registro já com o id.

        Tudo por NOME (`*`) de propósito: `create("Ana", "a@b.c", h)`
        na ordem errada gravaria trocado, e o erro só apareceria
        depois, no dado.
        """

        users_model = _users_model()

        # O Model entra aqui, montado campo a campo — nunca por
        # `**dados` de fora (SOLAR-ARCH-029).
        user = users_model(
            name_user=name,
            email_user=email,
            password_user=password_hash
        )

        session = self.database.session()

        session.add(user)

        # `commit` confirma a transação. Sem ele o objeto fica só na
        # sessão: nada chega ao banco quando a sessão fecha.
        session.commit()

        return user

    def email_exists(self, email: str) -> bool:
        """
        Indica se já existe usuário com o e-mail informado.
        """

        # `session.query` e não `select(...)`: o `select` viria de
        # `sqlalchemy`, e importar a tecnologia aqui quebraria a
        # SOLAR-ARCH-010. A consulta é montada com o Model, que
        # chegou pela fachada.
        users_model = _users_model()

        return (
            self.database.session()
            .query(users_model)
            .filter(users_model.email_user == email)
            .first()
            is not None
        )
