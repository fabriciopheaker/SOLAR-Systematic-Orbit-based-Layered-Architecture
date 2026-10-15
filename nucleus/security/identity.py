# Identidade da aplicação: SECRET_KEY e SOLAR_ID.
#
# É o primeiro mecanismo que o Kernel monta, e é o único ponto da
# arquitetura que ESCREVE no `.env`. A razão: o segredo precisa
# sobreviver ao reinício, e gerar uma chave nova a cada subida
# invalidaria toda sessão assinada com a anterior.
#
# Os dois valores têm papéis diferentes: `SECRET_KEY` é SEGREDO (assina),
# `SOLAR_ID` é IDENTIFICADOR (só nomeia a aplicação em log e auditoria).
import os
import secrets
import uuid


class Identity:
    """
    Gerencia a identidade criptográfica e a identidade única da aplicação
    dentro da arquitetura SOLAR.

    A Identity é responsável por garantir que a aplicação possua:

    - SECRET_KEY: segredo criptográfico utilizado pela aplicação;
    - SOLAR_ID: identificador único e não secreto da aplicação.

    Esses valores são persistidos no arquivo de ambiente para que sejam
    mantidos entre as reinicializações da aplicação.

    A SECRET_KEY deve permanecer secreta.
    O SOLAR_ID não possui caráter secreto e serve para identificar
    unicamente a aplicação em contextos como logs, auditoria, eventos
    e comunicação entre serviços.
    """

    # `SECRET_KEY` e `SOLAR_ID` são os NOMES das chaves no ambiente —
    # não são os valores.
    # solar:allow-secret (nome da chave no ambiente, não o valor)
    SECRET_KEY = "SECRET_KEY"
    SOLAR_ID = "SOLAR_ID"

    def __init__(self, env_file=".env"):
        # Caminho do arquivo de ambiente: injetável para o teste usar um
        # arquivo temporário em vez do `.env` do projeto.
        self.env_file = env_file

        # `None` = "ainda não lido". É esse estado que `init` procura para
        # decidir se gera um valor novo.
        self.secret_key = None
        self.solar_id = None

    def init(self):
        """
        Inicializa a identidade da aplicação.

        Caso SECRET_KEY ou SOLAR_ID já existam no ambiente, seus valores
        são preservados.

        Caso algum deles não exista, um novo valor é gerado e persistido
        no arquivo de ambiente.
        """

        # Lê o que já existe: PRESERVAR o valor anterior é o ponto. Uma
        # chave nova a cada subida invalidaria toda sessão assinada com
        # a anterior.
        self._load_environment()

        # `if not ...`: só gera quando não havia valor.
        if not self.secret_key:
            self.secret_key = self._generate_secret_key()

        if not self.solar_id:
            self.solar_id = self._generate_solar_id()

        # Grava SEMPRE, e não só quando gerou: se o `.env` perdeu a
        # linha por edição manual, ela volta.
        self._persist()

        return {
            self.SECRET_KEY: self.secret_key,
            self.SOLAR_ID: self.solar_id
        }

    def _load_environment(self):
        """
        Carrega SECRET_KEY e SOLAR_ID existentes no ambiente.
        """

        self.secret_key = os.getenv(self.SECRET_KEY)
        self.solar_id = os.getenv(self.SOLAR_ID)

    @staticmethod
    def _generate_secret_key():
        """
        Gera uma chave criptograficamente segura.
        """

        # `secrets` e não `random`: `random` é previsível a partir de
        # algumas saídas, e esta chave ASSINA sessão. 32 bytes viram 64
        # caracteres hexadecimais.
        return secrets.token_hex(32)

    @staticmethod
    def _generate_solar_id():
        """
        Gera um identificador único para a aplicação.

        O identificador não é um segredo.
        """

        # `uuid4` é aleatório (não deriva da máquina), e `str` porque o
        # valor vai para o `.env` como texto.
        return str(uuid.uuid4())

    def _persist(self):
        """
        Persiste SECRET_KEY e SOLAR_ID no arquivo de ambiente.
        """

        # Conferir ANTES de ler: sem isso o erro sairia do `open`, com
        # mensagem do sistema e sem dizer qual arquivo a aplicação
        # esperava encontrar.
        if not os.path.exists(self.env_file):
            raise FileNotFoundError(
                f"O arquivo {self.env_file} não foi encontrado."
            )

        # Lê tudo para a MEMÓRIA e reescreve no fim: o arquivo é
        # pequeno, e editar linha a linha no disco seria mais código
        # para o mesmo resultado.
        with open(self.env_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

        values = {
            self.SECRET_KEY: self.secret_key,
            self.SOLAR_ID: self.solar_id
        }

        # Acompanha quais chaves foram ENCONTRADAS no arquivo: o que
        # sobrar é acrescentado no fim.
        existing = set()

        # `startswith(f"{key}=")` com o `=` JUNTO: sem ele, uma chave
        # `SECRET_KEY_BACKUP` casaria com `SECRET_KEY`.
        for index, line in enumerate(lines):

            stripped = line.strip()

            for key, value in values.items():

                if stripped.startswith(f"{key}="):
                    # Substitui a LINHA, preservando a posição dela no
                    # arquivo — comentários e ordem continuam legíveis.
                    lines[index] = f"{key}={value}\n"
                    existing.add(key)

        for key, value in values.items():

            if key not in existing:
                lines.append(f"{key}={value}\n")

        # `writelines` (e não `write`) porque cada item da lista já veio
        # com o seu `\n`.
        with open(self.env_file, "w", encoding="utf-8") as file:
            file.writelines(lines)