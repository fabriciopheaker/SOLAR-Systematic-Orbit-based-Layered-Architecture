# Leitura e normalização das variáveis de ambiente.
#
# É um MECANISMO do Nucleus, e não uma camada: o que ele faz é ler o
# `.env` do ambiente ativo e devolver um dicionário de configuração para
# o Kernel montar a aplicação. Ele não conhece nenhum componente da
# arquitetura.
import os

from dotenv import load_dotenv

from nucleus.exceptions.solar_exception import SolarException


class Environment:
    """
    Lê e normaliza as variáveis de ambiente da aplicação.

    O Environment apenas lê e normaliza as variáveis do arquivo .env.

    Ele NÃO monta a URL de conexão, NÃO decide o dialect/driver e
    NÃO interpreta as configurações específicas de banco de dados.

    Essas responsabilidades pertencem ao DriverSQLAlchemy.
    """

    # Os três ambientes conhecidos. Um `APP_ENV` fora daqui é ERRO de
    # configuração, e não um valor a ser aceito em silêncio — daí o
    # `raise` em `init`.
    SUPPORTED_ENVIRONMENTS = {'DEV', 'TEST', 'PROD'}

    @staticmethod
    def init():

        """
            Configura a aplicação com base no ambiente,
            carregando e normalizando as variáveis correspondentes
            do arquivo .env.
        """

        # Carrega o `.env` para o processo. Sem isso, o `os.getenv` da
        # linha seguinte devolveria `None` e a aplicação nem saberia
        # dizer em que ambiente está.
        load_dotenv()

        environment = os.getenv('APP_ENV')

        if environment not in Environment.SUPPORTED_ENVIRONMENTS:
            raise SolarException(
                f"Ambiente '{environment}' não suportado.",
                code="INVALID_ENVIRONMENT"
            )

        # Dicionário de configuração: é ele que o Kernel guarda e que o
        # resto do Nucleus consulta por chave. As chaves são NOMES
        # LÓGICOS (`DB_HOST`), e não as variáveis do `.env`
        # (`DEV_DB_HOST`) — o prefixo do ambiente fica só na leitura.
        return {
            'APP_ENV': environment,

            # Configuração bruta do banco de dados.
            # A interpretação pertence ao DriverSQLAlchemy.
            'DB_CONNECTION': Environment.__read(
                environment, 'DB_CONNECTION'
            ),

            'DB_NAME': Environment.__read(
                environment, 'DB_NAME'
            ),

            'DB_HOST': Environment.__read(
                environment, 'DB_HOST'
            ),

            'DB_PORT': Environment.__read(
                environment, 'DB_PORT'
            ),

            'DB_USER': Environment.__read(
                environment, 'DB_USER'
            ),

            'DB_PASS': Environment.__read(
                environment, 'DB_PASS'
            ),

            'CORS': Environment.__read(
                environment, 'CORS_ORIGINS'
            ),

            'PORT': Environment.__read(
                environment, 'PORT'
            ),

            'HOST': Environment.__read(
                environment, 'HOST'
            ),
        }

    @staticmethod
    def __read(environment: str, key: str):
        """
            Lê e normaliza uma variável do ambiente atual.

            Valores vazios são normalizados para None.
        """

        # O PREFIXO do ambiente é o que permite os três estarem no mesmo
        # `.env`: `DEV_DB_HOST`, `TEST_DB_HOST`, `PROD_DB_HOST`.
        value = os.getenv(f"{environment}_{key}")

        if value is None:
            return None

        # `strip()`: espaço em volta de valor no `.env` é acidente de
        # digitação, e sem isso a URL de conexão sairia com espaço no
        # meio.
        value = value.strip()

        # `value or None`: variável DECLARADA mas VAZIA vira `None`. É o
        # caso de `PROD_HOST=` — declarada para ficar visível, ainda sem
        # valor.
        return value or None