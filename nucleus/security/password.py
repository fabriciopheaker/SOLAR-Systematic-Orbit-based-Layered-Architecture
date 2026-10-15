"""
Hash e verificação de senha.

A senha nunca é guardada, nem de forma cifrada: guarda-se o HASH.
Quem lê o banco não consegue voltar à senha — é o que torna o
vazamento do banco bem menos grave do que ele poderia ser.

Chamado na CLASSE: `Password.hash(...)`, e não em instância. Não
há `@staticmethod`, então uma instância passaria `self` no lugar
da senha e quebraria.
"""

import bcrypt


class Password:

    def hash(password: str) -> str:
        """
        Gera o hash de uma senha e retorna o hash como string.
        """

        # Salt NOVO a cada chamada. É o que faz a mesma senha
        # produzir hashes diferentes em usuários diferentes — sem
        # isso, duas senhas iguais apareceriam iguais no banco, e
        # uma tabela pré-calculada quebraria as duas de uma vez.
        salt = bcrypt.gensalt()

        # O custo do bcrypt é proposital: cada tentativa de
        # adivinhar custa tempo de processamento para quem ataca.
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

        return hashed.decode("utf-8")

    def verify(password: str, hashed_password: str) -> bool:
        """
        Verifica se a senha fornecida corresponde ao hash armazenado.
        """

        # O bcrypt guarda o salt DENTRO do próprio hash: é por isso
        # que não há nada além da senha e do hash aqui.
        #
        # A comparação é feita pelo bcrypt, que não para no primeiro
        # byte diferente. Comparar com `==` deixaria medir, pelo
        # tempo de resposta, quantos caracteres do hash acertamos.
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )