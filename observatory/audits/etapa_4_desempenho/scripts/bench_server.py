"""Servidor isolado para a auditoria de desempenho da Etapa 4.

Não altera o código de produção: monta o Kernel e o Server reais,
mas com configuração TEST, SQLite temporário, storage temporário e
arquivo de ambiente temporário.

Uso (chamado por run_benchmark.py):
    py observatory/audits/etapa_4/bench_server.py --workdir <dir>
"""

from __future__ import annotations

import json
import platform
import sys
import threading
import time
from pathlib import Path

T0 = time.perf_counter()

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from werkzeug.serving import make_server  # noqa: E402

from nucleus.kernel import Kernel  # noqa: E402
from observatory.log.error_log import ErrorLog  # noqa: E402

IMPORT_MS = (time.perf_counter() - T0) * 1000


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()

    workdir = Path(args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    tmp = workdir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    storage = tmp / "storage"
    storage.mkdir(parents=True, exist_ok=True)

    sqlite_path = (tmp / "bench.sqlite").resolve()
    if sqlite_path.exists():
        sqlite_path.unlink()

    env_file = tmp / ".env"
    env_file.write_text("APP_ENV=TEST\n", encoding="utf-8")

    config = {
        "APP_ENV": "TEST",
        "DB_CONNECTION": "sqlite",
        # SQLAlchemy no Windows aceita caminho absoluto com barras
        # normais; é o mesmo banco de arquivo usado pelo processo.
        "DB_NAME": sqlite_path.as_posix(),
        "DB_HOST": None,
        "DB_PORT": None,
        "DB_USER": None,
        "DB_PASS": None,
        "CORS": None,
        "HOST": "127.0.0.1",
        "PORT": "0",
    }

    kernel = Kernel(
        env_file=env_file,
        config=config,
        storage_root=storage,
    )

    mount_start = time.perf_counter()
    app = kernel.mount()

    error_log = ErrorLog(
        path=tmp / "error_log.sqlite",
        solar_id=kernel.identity.solar_id,
        environment=kernel.config.get("APP_ENV"),
    )
    kernel.observe(error_log)

    mount_ms = (time.perf_counter() - mount_start) * 1000

    bind_start = time.perf_counter()
    httpd = make_server("127.0.0.1", 0, app, threaded=True)
    bind_ms = (time.perf_counter() - bind_start) * 1000

    ready = {
        "pid": __import__("os").getpid(),
        "host": "127.0.0.1",
        "port": httpd.server_port,
        "sqlite_path": str(sqlite_path),
        "python": sys.version,
        "platform": platform.platform(),
        "import_ms": round(IMPORT_MS, 3),
        "mount_ms": round(mount_ms, 3),
        "bind_ms": round(bind_ms, 3),
        "ready_ms": round((time.perf_counter() - T0) * 1000, 3),
    }

    ready_path = workdir / "startup.json"
    tmp_ready = ready_path.with_suffix(".json.tmp")
    tmp_ready.write_text(
        json.dumps(ready, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp_ready.replace(ready_path)

    print("BENCH_READY " + json.dumps(ready, ensure_ascii=False), flush=True)

    def wait_for_stop() -> None:
        # O pai envia uma linha (normalmente "stop") quando termina.
        try:
            sys.stdin.readline()
        finally:
            httpd.shutdown()

    threading.Thread(target=wait_for_stop, daemon=True).start()

    try:
        httpd.serve_forever()
    finally:
        try:
            kernel.shutdown()
        finally:
            error_log.close()
            httpd.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
