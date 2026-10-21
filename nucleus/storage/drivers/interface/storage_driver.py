"""
Contrato do driver de armazenamento.

A fachada `Storage` fala com qualquer driver que implemente isto.
O contrato é genérico de propósito: a referência que `save`
devolve é interpretada pelo PRÓPRIO driver (caminho local, chave
de objeto na nuvem), e quem a guarda é a aplicação.
"""

from abc import ABC, abstractmethod


class StorageDriver(ABC):
    """
    Contrato de armazenamento de arquivos da SOLAR.

    Um StorageDriver é responsável por gravar, ler, verificar e
    remover arquivos, sem que a aplicação conheça ONDE eles são
    armazenados.

    Implementações previstas:

        LocalStorageDriver    → pasta `storage/` da aplicação
        CloudStorageDriver    → S3, GCS, Azure Blob, ... (futuro)

    A aplicação conhece apenas este contrato e a fachada
    `nucleus.storage.storage.Storage`.

    O driver NÃO interpreta o conteúdo do arquivo: sanitização e
    validação da ENTRADA pertencem ao pipeline da
    SOLAR-ROF-001 (Sanitizer/Validator).
    """

    # `name` é o nome LÓGICO (o que a aplicação escolheu) — o
    # caminho físico é problema do driver. `bytes` e não stream:
    # o pipeline de upload já validou e sanitizou o conteúdo, e
    # ele cabe em memória.
    @abstractmethod
    def save(self, name: str, content: bytes) -> str:
        """
        Armazena o conteúdo sob o nome informado.

        Retorna a REFERÊNCIA do arquivo armazenado:

            driver local → caminho relativo (ex.: "documents/a.pdf")
            driver nuvem → chave/objeto (ex.: "s3://bucket/a.pdf")

        É essa referência que a aplicação guarda.
        """
        raise NotImplementedError

    @abstractmethod
    def read(self, name: str) -> bytes:
        """
        Retorna o conteúdo armazenado sob o nome informado.

        Deve lançar StorageException quando o arquivo não existir.
        """
        raise NotImplementedError

    # Existe separado do `read` porque responder "pode apagar?" não
    # pode obrigar a carregar o arquivo inteiro.
    @abstractmethod
    def exists(self, name: str) -> bool:
        """
        Indica se existe arquivo armazenado com o nome informado.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, name: str) -> None:
        """
        Remove o arquivo armazenado sob o nome informado.
        """
        raise NotImplementedError
