"""
A entidade do usuário que este Planet cria.

Entidade é o dado de DOMÍNIO: o que a aplicação decidiu que um
usuário é. Ela não conhece HTTP, não conhece tabela e não sabe se
salvar — quem sabe é a Persistence.
"""

from nucleus.exceptions.validation_exception import ValidationException
from nucleus.security.password import Password


class UserEntity:
    """
    O usuário pronto para ser gravado.

    A entidade nasce do CONTRATO de entrada, e já com o hash: a senha
    em texto puro não passa do construtor.

    O campo é `senha_hash`, e não a senha. A senha em texto puro existe
    só entre a entrada e o `Password.hash` — guardar o hash aqui é o
    que impede o texto de vazar para o Resource, para o log ou para uma
    mensagem de erro.
    """

    # Códigos estáveis: quem trata a resposta distingue os casos sem
    # ler a mensagem.
    INVALID_EMAIL = "INVALID_EMAIL"
    EMAIL_TAKEN = "EMAIL_TAKEN"

    def __init__(self, data):
        # O HASH acontece aqui. A senha em texto puro existe só entre a
        # entrada e esta linha — nada abaixo daqui a vê.
        self.nome = data.nome
        self.email = data.email
        self.senha_hash = Password.hash(data.senha)

    @classmethod
    def ensure_email_is_valid(cls, email: str) -> None:
        """
        Recusa e-mail sem a forma mínima de e-mail.

        A validação mora aqui, na entidade, porque é regra de
        NEGÓCIO: o que é um e-mail válido não depende de HTTP nem de
        banco — depende do domínio.
        """

        # Checagem mínima e honesta: um `@`, com algo dos dois lados e
        # um ponto no domínio.
        #
        # Perseguir o e-mail "válido" com uma expressão regular
        # completa é um clássico que acaba recusando endereço
        # legítimo — e o que confirma um e-mail é a mensagem que chega
        # nele.
        local, separator, domain = email.partition("@")

        if not separator or not local or "." not in domain:

            raise ValidationException(
                f"O e-mail '{email}' não tem formato válido.",
                code=cls.INVALID_EMAIL
            )

    @classmethod
    def verify_email(cls, already_taken: bool) -> None:
        """
        Recusa o e-mail que já pertence a outro usuário.

        Quem CONSULTA o banco é o UseCase — é ele que fala com o
        Repository. Decidir que e-mail duplicado não pode é invariante
        do domínio, e por isso mora aqui.

        O parâmetro é o RESULTADO da consulta, e não o e-mail: assim a
        entidade não precisa saber que existe um banco para consultar.
        """

        if already_taken:

            raise ValidationException(
                "Já existe usuário com este e-mail.",
                code=cls.EMAIL_TAKEN
            )