import sqlite3
import traceback
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from observatory.records.error_record import ErrorRecord
from observatory.solar.audit import TIME_ZONE


# Onde o banco do Observatório vive, por padrão.
#
# Arquivo PRÓPRIO, separado do banco da aplicação: o Observatório
# observa a aplicação, não faz parte dela.
DEFAULT_DIRECTORY = Path(__file__).resolve().parent.parent / "data"
DEFAULT_FILENAME = "solar.sqlite"

MOMENT_FORMAT = "%Y-%m-%d %H:%M:%S"


class ErrorLog:
    """
    Registro de erros da aplicação, em banco SQLite próprio.

    O problema que isto resolve: depois que o erro foi tratado e
    a resposta genérica saiu, o detalhe some. Aqui ele FICA — com
    o contexto necessário para investigar depois.

    Quem grava é o `ErrorHandler`, através do gancho de
    observação:

        log = ErrorLog(solar_id=..., environment=...)

        handler = ErrorHandler(observers=[log])

        try:
            ...
        except Exception as error:
            return handler.handle(error, {
                "method": request.method,
                "route": request.path,
                "status": 500,
            })

    A DIREÇÃO da dependência é Observatory → Nucleus: o Nucleus
    NÃO conhece esta classe. Quem liga os dois é o arranque da
    aplicação, e o `ErrorHandler` só sabe que existe um callable
    interessado no erro.

    Falhar aqui NÃO derruba o fluxo tratado: registrar é
    best-effort, porque o Observatório observa e não participa.
    """

    TABLE = "error_log"

    UNKNOWN_CODE = "UNKNOWN"

    # Colunas na ordem em que são gravadas.
    COLUMNS = (
        "moment",
        "code",
        "message",
        "reference",
        "exception_type",
        "detail",
        "method",
        "route",
        "status",
        "solar_id",
        "environment",
    )

    SCHEMA = (
        "CREATE TABLE IF NOT EXISTS error_log ("
        "number INTEGER PRIMARY KEY AUTOINCREMENT,"
        "moment TEXT NOT NULL,"
        "code TEXT NOT NULL DEFAULT '',"
        "message TEXT NOT NULL DEFAULT '',"
        "reference TEXT NOT NULL DEFAULT '',"
        "exception_type TEXT NOT NULL DEFAULT '',"
        "detail TEXT NOT NULL DEFAULT '',"
        "method TEXT NOT NULL DEFAULT '',"
        "route TEXT NOT NULL DEFAULT '',"
        "status INTEGER NOT NULL DEFAULT 0,"
        "solar_id TEXT NOT NULL DEFAULT '',"
        "environment TEXT NOT NULL DEFAULT ''"
        ")"
    )

    def __init__(
        self,
        path: str | Path | None = None,
        solar_id: str = "",
        environment: str = "",
        clock: Callable[[], str] | None = None
    ):
        self.path = (
            Path(path)
            if path is not None
            else DEFAULT_DIRECTORY / DEFAULT_FILENAME
        )

        self.solar_id = solar_id
        self.environment = environment

        self._clock = clock or self._moment

        self.path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = self._connect()

    # -----------------------------------------------------------------
    # Gancho de observação
    # -----------------------------------------------------------------

    def __call__(
        self,
        error: BaseException,
        payload: Mapping | None = None,
        context: Mapping | None = None
    ) -> ErrorRecord | None:
        """
        Assinatura de OBSERVADOR do `ErrorHandler`.

        Devolve o registro gravado, ou None quando a gravação
        falhou — o erro tratado segue o caminho dele.
        """

        try:
            return self.record(error, payload, context)

        except sqlite3.Error:
            return None

    # -----------------------------------------------------------------
    # Gravação
    # -----------------------------------------------------------------

    def record(
        self,
        error: BaseException,
        payload: Mapping | None = None,
        context: Mapping | None = None
    ) -> ErrorRecord:
        """
        Grava um erro e devolve o registro, já com o número.
        """

        data = payload or {}
        fields = context or {}

        entry = ErrorRecord(
            moment=self._clock(),
            code=str(data.get("code") or self.UNKNOWN_CODE),
            message=str(data.get("message") or ""),
            reference=str(data.get("reference") or ""),
            exception_type=type(error).__name__,
            detail=self._detail(error),
            method=str(fields.get("method") or ""),
            route=str(fields.get("route") or ""),
            status=int(fields.get("status") or 0),
            solar_id=self.solar_id,
            environment=self.environment
        )

        return replace(entry, number=self._insert(entry))

    def _insert(self, entry: ErrorRecord) -> int:
        """
        Insere a linha e devolve o número gerado.

        Os valores vão como PARÂMETROS ligados ao SQL (`?`),
        nunca interpolados no texto.
        """

        columns = ", ".join(self.COLUMNS)
        parameters = ", ".join("?" for _ in self.COLUMNS)

        cursor = self._connection.execute(
            f"INSERT INTO {self.TABLE} ({columns}) "
            f"VALUES ({parameters})",
            tuple(getattr(entry, column) for column in self.COLUMNS)
        )

        self._connection.commit()

        return int(cursor.lastrowid or 0)

    @staticmethod
    def _detail(error: BaseException) -> str:
        """
        Rastro completo do ocorrido, para investigação.
        """

        return "".join(
            traceback.format_exception(
                type(error),
                error,
                error.__traceback__
            )
        )

    # -----------------------------------------------------------------
    # Leitura
    # -----------------------------------------------------------------

    def all(self) -> list[ErrorRecord]:
        """
        Todos os registros, do mais antigo para o mais recente.
        """

        cursor = self._connection.execute(
            f"SELECT * FROM {self.TABLE} ORDER BY number"
        )

        return [
            self._to_record(row)
            for row in cursor.fetchall()
        ]

    def find(self, reference: str) -> ErrorRecord | None:
        """
        O registro de uma referência, ou None.
        """

        cursor = self._connection.execute(
            f"SELECT * FROM {self.TABLE} WHERE reference = ? "
            f"ORDER BY number DESC LIMIT 1",
            (str(reference),)
        )

        row = cursor.fetchone()

        return self._to_record(row) if row is not None else None

    def count(self) -> int:
        """
        Quantos erros foram registrados.
        """

        cursor = self._connection.execute(
            f"SELECT COUNT(*) FROM {self.TABLE}"
        )

        return int(cursor.fetchone()[0])

    def close(self) -> None:
        """
        Fecha a conexão.
        """

        self._connection.close()

    # -----------------------------------------------------------------
    # Interno
    # -----------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """
        Abre a conexão e garante a tabela.
        """

        connection = sqlite3.connect(str(self.path))

        connection.row_factory = sqlite3.Row

        connection.execute(self.SCHEMA)
        connection.commit()

        return connection

    @staticmethod
    def _moment() -> str:
        """
        Momento atual, no fuso do Observatório.
        """

        return datetime.now(TIME_ZONE).strftime(MOMENT_FORMAT)

    @staticmethod
    def _to_record(row: sqlite3.Row) -> ErrorRecord:
        """
        Converte a linha do banco no registro do Observatório.
        """

        return ErrorRecord(
            number=int(row["number"]),
            moment=str(row["moment"]),
            code=str(row["code"]),
            message=str(row["message"]),
            reference=str(row["reference"]),
            exception_type=str(row["exception_type"]),
            detail=str(row["detail"]),
            method=str(row["method"]),
            route=str(row["route"]),
            status=int(row["status"]),
            solar_id=str(row["solar_id"]),
            environment=str(row["environment"])
        )
