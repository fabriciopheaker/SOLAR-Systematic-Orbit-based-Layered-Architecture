from datetime import datetime, timezone
from nucleus.database.database import Database


class Users(Database.orm):
    """
    Model ORM responsável pelo mapeamento da tabela users.

    Este Model representa a estrutura da tabela no banco de dados.
    Regras de negócio e regras de domínio não devem ser implementadas aqui.
    """

    __tablename__ = "users"

    id_user = Database.model.Column(
        Database.model.Integer,
        primary_key=True,
        autoincrement=True
    )

    name_user = Database.model.Column(
        Database.model.String(100),
        nullable=False
    )

    email_user = Database.model.Column(
        Database.model.String(255),
        nullable=False,
        unique=True
    )

    password_user = Database.model.Column(
        Database.model.String(250),
        nullable=False
    )


    # Indica se o usuário precisa redefinir a senha.
    reset_password_user = Database.model.Column(
        Database.model.Enum(
            "true",
            "false",
            name="reset_password_enum"
        ),
        default="false"
    )

    # Data de criação do usuário.
    data_created_user = Database.model.Column(
        Database.model.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Data da última atualização do usuário.
    data_updated_user = Database.model.Column(
        Database.model.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Data de exclusão lógica do usuário.
    data_deleted_user = Database.model.Column(
        Database.model.DateTime,
        nullable=True,
        default=None
    )


    def __repr__(self):
        return f"<Usuarios {self.name_user}>"