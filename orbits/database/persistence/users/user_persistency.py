

from nucleus.database.database import Database
from orbits.database.models.user_model import Users
from orbits.database.persistence.users.output.create_user_output import CreateUserOutput


class UserPersistency:

    def __init__(self, database: type[Database]):
        self.database = database

    def create(self, data):
        user = Users(
            name_user=data.nome,
            email_user=data.email,
            password_user=data.senha_hash
        )

        session = self.database.session()

        try:
            session.add(user)
            session.commit()

        except Exception:
            session.rollback()
            raise


        return CreateUserOutput.to_object(user)

    def email_exists(self, email: str) -> bool:
        return (
            self.database.session()
            .query(Users)
            .filter(Users.email_user == email)
            .first()
            is not None
        )


user_persistency = UserPersistency(Database)
