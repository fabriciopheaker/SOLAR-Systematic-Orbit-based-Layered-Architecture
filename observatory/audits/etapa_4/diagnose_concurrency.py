"""Diagnóstico: reproduz a criação concorrente sem HTTP.

Não altera produção. Apenas exercita o mesmo UseCase e a mesma
sessão SQLAlchemy compartilhada usados pela rota POST.
"""

from __future__ import annotations

import tempfile
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path

import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nucleus.kernel import Kernel


CONFIG = {
    "APP_ENV": "TEST",
    "DB_CONNECTION": "sqlite",
    "DB_NAME": "",
    "DB_HOST": None,
    "DB_PORT": None,
    "DB_USER": None,
    "DB_PASS": None,
    "CORS": None,
    "HOST": "127.0.0.1",
    "PORT": "0",
}


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        sqlite = root / "diag.sqlite"
        config = dict(CONFIG, DB_NAME=sqlite.as_posix())
        env_file = root / ".env"
        env_file.write_text("APP_ENV=TEST\n", encoding="utf-8")

        kernel = Kernel(
            env_file=env_file,
            config=config,
            storage_root=root / "storage",
        )
        kernel.mount()

        from orbits.planets.example.controllers.inputs.create_user_input import (
            CreateUserInput,
        )
        from orbits.planets.example.usecases.create_user_usecase import (
            create_user_use_case,
        )

        errors: list[str] = []
        executed = 0
        lock = threading.Lock()

        def worker(index: int) -> None:
            nonlocal executed
            for seq in range(10):
                payload = CreateUserInput({
                    "nome": f"Diag {index}-{seq}",
                    "email": f"diag-{index}-{seq}@example.com",
                    "senha": "S3nha!bench",
                })
                try:
                    create_user_use_case.execute(payload)
                except Exception:
                    with lock:
                        errors.append(traceback.format_exc())
                finally:
                    with lock:
                        executed += 1

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        print(f"erros={len(errors)}")
        if errors:
            print(errors[0][-3000:])

        result = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "threads": 8,
            "calls_per_thread": 10,
            "executed": executed,
            "errors": len(errors),
            "error_rate": round(len(errors) / executed, 4) if executed else None,
            "first_traceback_tail": errors[0][-3000:] if errors else None,
        }
        output = HERE.parent / "RESULTADOS_BRUTOS" / "diagnostico_concorrencia.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        try:
            kernel.shutdown()
        except Exception:
            # A sessão compartilhada pode estar em estado inválido após
            # os erros; o encerramento não é objeto deste diagnóstico.
            pass


if __name__ == "__main__":
    main()
