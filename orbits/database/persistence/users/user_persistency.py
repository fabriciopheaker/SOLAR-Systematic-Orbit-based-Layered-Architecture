

from nucleus.database.database import Database
from orbits.database.models.user_model import Users
from orbits.database.persistence.users.output.create_user_output import CreateUserOutput


class UserPersistency:

    def __init__(self, database: type[Database]):
        self.database = database

    def create( self, data) :

        user = Users(
            name_user=data.name,
            email_user=data.email,
            password_user=data.password_hash
        )

        session = self.database.session()

        try:
            session.add(user)

            # `commit` confirma a transação. Sem ele o objeto fica só
            # na sessão: nada chega ao banco quando a sessão fecha.
            session.commit()

        except Exception:
            # A transação é responsabilidade desta camada: se a
            # gravação falhar, a sessão não pode seguir marcada como
            # pendente para a próxima operação.
            session.rollback()
            raise
        

        return CreateUserOutput.to_object(user)

    def email_exists(self, email: str) -> bool:
        """
        Indica se já existe usuário com o e-mail informado.
        """

        # `session.query` e não `select(...)`: o `select` viria de
        # `sqlalchemy`, e importar a tecnologia aqui quebraria a
        # SOLAR-ARCH-010. A consulta é montada com o Model, que
        # chegou pela fachada.
        return (
            self.database.session()
            .query(Users)
            .filter(Users.email_user == email)
            .first()
            is not None
        )
