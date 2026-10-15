from pathlib import Path

from nucleus.exceptions.storage_exception import StorageException
from nucleus.storage.drivers.interface.storage_driver import StorageDriver


class LocalStorageDriver(StorageDriver):
    """
    Driver de armazenamento LOCAL da SOLAR.

    Grava os arquivos em uma pasta da própria aplicação
    (por padrão `storage/`):

        LocalStorageDriver()                    → storage/
        LocalStorageDriver(root="/solar/files") → /solar/files

    O nome informado pode conter subpastas:

        save("documents/2026/contrato.pdf", conteudo)

    SEGURANÇA: o nome NÃO pode escapar da raiz do storage
    (ex.: "../../etc/passwd"). Tentativas lançam StorageException.
    """

    def __init__(
        self,
        root: str | Path = "storage",
        create: bool = True
    ):
        self.root = Path(root)

        if create:
            self.root.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, content: bytes) -> str:
        """
        Grava o conteúdo e retorna o caminho relativo à raiz.
        """

        path = self._resolve(name)

        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            path.write_bytes(content)

        except OSError as error:
            raise StorageException(
                f"Falha ao armazenar '{name}'.",
                code="STORAGE_SAVE_ERROR"
            ) from error

        return path.relative_to(self._root()).as_posix()

    def read(self, name: str) -> bytes:
        path = self._resolve(name)

        if not path.is_file():
            raise StorageException(
                f"Arquivo '{name}' não encontrado.",
                code="STORAGE_NOT_FOUND"
            )

        return path.read_bytes()

    def exists(self, name: str) -> bool:
        return self._resolve(name).is_file()

    def delete(self, name: str) -> None:
        path = self._resolve(name)

        # Apagar o que já não existe é SUCESSO, não erro: o
        # resultado pretendido foi alcançado. `read` é diferente —
        # lá o arquivo É o resultado.
        if path.is_file():
            path.unlink()

    def _root(self) -> Path:
        return self.root.resolve()

    def _resolve(self, name: str) -> Path:
        """
        Converte o nome informado em caminho absoluto, garantindo
        que ele permaneça DENTRO da raiz do storage.
        """

        if not name or not name.strip():
            raise StorageException(
                "O nome do arquivo é obrigatório.",
                code="INVALID_STORAGE_NAME"
            )

        root = self._root()
        path = (root / name).resolve()

        # A defesa contra path traversal.
        #
        # `resolve()` elimina `.` e `..` ANTES da conferência: sem
        # ele, "../../etc/passwd" pareceria começar com a raiz. A
        # conferência é sobre o caminho FINAL, e não sobre o texto
        # que chegou.
        if path != root and root not in path.parents:
            raise StorageException(
                f"O nome '{name}' escapa da raiz do storage.",
                code="STORAGE_PATH_ESCAPE"
            )

        return path
