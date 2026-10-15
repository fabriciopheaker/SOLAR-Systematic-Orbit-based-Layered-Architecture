from nucleus.exceptions.contract_exception import ContractException
from nucleus.exceptions.storage_exception import StorageException
from nucleus.storage.drivers.interface.storage_driver import StorageDriver


class Storage:
    """
    Fachada de armazenamento de arquivos da SOLAR.

    A aplicação NÃO conhece o driver: fala apenas com a fachada.
    O driver concreto (local, nuvem, ...) é injetado em `init`:

        Storage.init(LocalStorageDriver())
        Storage.save("documents/contrato.pdf", conteudo)

    Segue o mesmo padrão das outras fachadas do Nucleus
    (Database, Broadcast).
    """

    _driver: StorageDriver | None = None

    @classmethod
    def init(cls, driver: StorageDriver) -> None:
        """
        Inicializa o mecanismo de armazenamento da aplicação.

        O driver recebido deve implementar o contrato StorageDriver.
        """

        if not isinstance(driver, StorageDriver):
            raise ContractException(
                "O driver fornecido não implementa o contrato "
                "StorageDriver.",
                code="INVALID_STORAGE_DRIVER"
            )

        cls._driver = driver

    @classmethod
    def save(cls, name: str, content: bytes) -> str:
        """
        Armazena o conteúdo e retorna a referência do arquivo.
        """

        # Toda operação passa por esta conferência. Sem driver, o
        # erro é "Storage não inicializado", com código estável —
        # e não um AttributeError em `None`, que não diz nada.
        cls._ensure_initialized()

        return cls._driver.save(name, content)

    @classmethod
    def read(cls, name: str) -> bytes:
        """
        Retorna o conteúdo do arquivo informado.
        """

        cls._ensure_initialized()

        return cls._driver.read(name)

    @classmethod
    def exists(cls, name: str) -> bool:
        """
        Indica se o arquivo informado existe no storage.
        """

        cls._ensure_initialized()

        return cls._driver.exists(name)

    @classmethod
    def delete(cls, name: str) -> None:
        """
        Remove o arquivo informado do storage.
        """

        cls._ensure_initialized()

        cls._driver.delete(name)

    @classmethod
    def _ensure_initialized(cls) -> None:
        """
        Garante que o Storage foi inicializado com um driver.
        """

        # Falha de MONTAGEM, não de uso: a aplicação subiu sem
        # chamar `Storage.init`.
        if cls._driver is None:
            raise StorageException(
                "O Storage ainda não foi inicializado.",
                code="STORAGE_NOT_INITIALIZED"
            )
