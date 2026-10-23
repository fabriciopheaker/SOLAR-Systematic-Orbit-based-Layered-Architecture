"""Servidor isolado para os testes de segurança da Etapa 5.

Monta a aplicação real com configuração TEST, SQLite temporário,
storage temporário e arquivo de ambiente temporário. Escuta apenas
em 127.0.0.1, em porta efêmera.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import threading
import time
from pathlib import Path

T0 = time.perf_counter()

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from werkzeug.serving import make_server  # noqa: E402

from nucleus.kernel import Kernel  # noqa: E402
from observatory.log.error_log import ErrorLog  # noqa: E402


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()

    workdir = Path(args.workdir).resolve()
    tmp = workdir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    sqlite_path = (tmp / "security.sqlite").resolve()
    if sqlite_path.exists():
        sqlite_path.unlink()

    env_file = tmp / ".env"
    env_file.write_text("APP_ENV=TEST\n", encoding="utf-8")

    config = {
        "APP_ENV": "TEST",
        "DB_CONNECTION": "sqlite",
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
        storage_root=tmp / "storage",
    )

    app = kernel.mount()

    error_log = ErrorLog(
        path=tmp / "error_log.sqlite",
        solar_id=kernel.identity.solar_id,
        environment=kernel.config.get("APP_ENV"),
    )
    kernel.observe(error_log)

    httpd = make_server("127.0.0.1", 0, app, threaded=True)

    ready = {
        "pid": os.getpid(),
        "host": "127.0.0.1",
        "port": httpd.server_port,
        "sqlite_path": str(sqlite_path),
        "python": sys.version,
        "platform": platform.platform(),
        "ready_ms": round((time.perf_counter() - T0) * 1000, 3),
    }

    ready_path = workdir / "startup.json"
    tmp_ready = ready_path.with_suffix(".json.tmp")
    tmp_ready.write_text(
        json.dumps(ready, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp_ready.replace(ready_path)

    print("SECURITY_READY " + json.dumps(ready, ensure_ascii=False), flush=True)

    def wait_for_stop() -> None:
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
