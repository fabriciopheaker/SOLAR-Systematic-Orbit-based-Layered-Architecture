import pytest

from nucleus.exceptions.contract_exception import ContractException
from nucleus.exceptions.storage_exception import StorageException
from nucleus.storage.drivers.local_storage_driver import LocalStorageDriver
from nucleus.storage.drivers.interface.storage_driver import StorageDriver
from nucleus.storage.storage import Storage


CONTENT = b"conteudo do documento"


# ---------------------------------------------------------------------
# LocalStorageDriver
# ---------------------------------------------------------------------

def test_local_driver_saves_and_reads(tmp_path):

    driver = LocalStorageDriver(root=tmp_path / "storage")

    reference = driver.save("documents/contrato.pdf", CONTENT)

    assert reference == "documents/contrato.pdf"
    assert driver.exists("documents/contrato.pdf")
    assert driver.read("documents/contrato.pdf") == CONTENT


# a pasta storage/ e criada automaticamente
def test_local_driver_creates_storage_directory(tmp_path):

    root = tmp_path / "storage"

    LocalStorageDriver(root=root)

    assert root.is_dir()


# subpastas no nome tambem sao criadas
def test_local_driver_creates_subdirectories(tmp_path):

    driver = LocalStorageDriver(root=tmp_path / "storage")

    driver.save("documents/2026/01/contrato.pdf", CONTENT)

    assert (
        tmp_path / "storage/documents/2026/01/contrato.pdf"
    ).is_file()


# leitura de arquivo inexistente e erro
def test_local_driver_read_missing_file_raises(tmp_path):

    driver = LocalStorageDriver(root=tmp_path / "storage")

    with pytest.raises(StorageException):
        driver.read("documents/inexistente.pdf")


# remocao de arquivo
def test_local_driver_deletes_file(tmp_path):

    driver = LocalStorageDriver(root=tmp_path / "storage")

    driver.save("documents/contrato.pdf", CONTENT)
    driver.delete("documents/contrato.pdf")

    assert driver.exists("documents/contrato.pdf") is False


# SEGURANCA: o nome nao pode escapar da raiz do storage
def test_local_driver_rejects_path_escape(tmp_path):

    driver = LocalStorageDriver(root=tmp_path / "storage")

    with pytest.raises(StorageException):
        driver.save("../fora.pdf", CONTENT)


def test_local_driver_rejects_empty_name(tmp_path):

    driver = LocalStorageDriver(root=tmp_path / "storage")

    with pytest.raises(StorageException):
        driver.save("", CONTENT)


# ---------------------------------------------------------------------
# Storage (fachada)
# ---------------------------------------------------------------------

def test_facade_delegates_to_driver(tmp_path, monkeypatch):

    monkeypatch.setattr(Storage, "_driver", None)

    Storage.init(LocalStorageDriver(root=tmp_path / "storage"))

    reference = Storage.save("documents/contrato.pdf", CONTENT)

    assert reference == "documents/contrato.pdf"
    assert Storage.exists("documents/contrato.pdf") is True
    assert Storage.read("documents/contrato.pdf") == CONTENT

    Storage.delete("documents/contrato.pdf")

    assert Storage.exists("documents/contrato.pdf") is False


# a fachada exige inicializacao
def test_facade_requires_initialization(monkeypatch):

    monkeypatch.setattr(Storage, "_driver", None)

    with pytest.raises(StorageException):
        Storage.save("documents/contrato.pdf", CONTENT)


# a fachada exige um driver que implemente o contrato
def test_facade_rejects_invalid_driver():

    with pytest.raises(ContractException):
        Storage.init("nao-e-um-driver")


# o contrato do driver e abstrato
def test_storage_driver_is_abstract():

    with pytest.raises(TypeError):
        StorageDriver()
