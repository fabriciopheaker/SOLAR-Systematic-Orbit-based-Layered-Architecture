"""Testes dinâmicos de segurança da Etapa 5.

Executa a aplicação real em processo separado, em 127.0.0.1, com
SQLite temporário e dados sintéticos. Não altera código de produção.

Uso:
    py observatory/audits/etapa_5/run_security_tests.py
"""

from __future__ import annotations

import http.client
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
WORKDIR = HERE.parent
RAW = WORKDIR / "RESULTADOS_BRUTOS"
SERVER = WORKDIR / "security_server.py"

HOST = "127.0.0.1"
TIMEOUT = 10.0

# Valores sintéticos do teste; não são credenciais reais.
FIXTURE_TEXT = "S3nha!audit"
FIXTURE_SHORT = "x"

SECURITY_HEADERS = (
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "Access-Control-Allow-Origin",
    "Content-Type",
    "Content-Length",
    "Allow",
    "Server",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_server() -> tuple[subprocess.Popen, dict]:
    RAW.mkdir(parents=True, exist_ok=True)
    ready_path = WORKDIR / "startup.json"
    if ready_path.exists():
        ready_path.unlink()

    log_path = RAW / "server.log"
    log_file = log_path.open("w", encoding="utf-8")

    process = subprocess.Popen(
        [sys.executable, str(SERVER), "--workdir", str(WORKDIR)],
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.time() + 40
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Servidor encerrou; veja {log_path}")
        if ready_path.exists():
            try:
                return process, json.loads(
                    ready_path.read_text(encoding="utf-8")
                )
            except json.JSONDecodeError:
                pass
        time.sleep(0.05)

    process.terminate()
    raise TimeoutError("Servidor não ficou pronto em 40 s.")


def stop_server(process: subprocess.Popen) -> None:
    try:
        if process.stdin and not process.stdin.closed:
            process.stdin.write("stop\n")
            process.stdin.flush()
    except Exception:
        pass

    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def call(
    host: str,
    port: int,
    method: str,
    path: str,
    body: str | bytes | None = None,
    headers: dict | None = None,
    store_body: bool = True,
) -> dict:
    connection = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
    all_headers = dict(headers or {})
    if body is not None and "Content-Type" not in all_headers:
        all_headers["Content-Type"] = "application/json"

    started = time.perf_counter()
    try:
        connection.request(method, path, body=body, headers=all_headers)
        response = connection.getresponse()
        raw = response.read()
        elapsed = (time.perf_counter() - started) * 1000

        text = raw.decode("utf-8", "replace")
        parsed = None
        try:
            parsed = json.loads(text) if text else None
        except json.JSONDecodeError:
            parsed = None

        selected = {
            name: response.getheader(name)
            for name in SECURITY_HEADERS
            if response.getheader(name) is not None
        }

        return {
            "status": response.status,
            "latency_ms": round(elapsed, 3),
            "headers": selected,
            "json": parsed,
            "body_preview": text[:300] if store_body else None,
            "body_length": len(raw),
        }
    finally:
        connection.close()


def db_connect(sqlite_path: str) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    for old in RAW.glob("*.json"):
        old.unlink()

    process, startup = start_server()
    host, port = startup["host"], startup["port"]
    sqlite_path = startup["sqlite_path"]

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results: list[dict] = []

    def add(
        test_id: str,
        category: str,
        description: str,
        method: str,
        path: str,
        body=None,
        headers=None,
        store_body: bool = True,
    ) -> dict:
        result = call(
            host, port, method, path, body=body, headers=headers,
            store_body=store_body,
        )
        result.update({
            "id": test_id,
            "category": category,
            "description": description,
            "request": {
                "method": method,
                "path": path,
                "headers": headers or {},
                "body_length": len(body) if body is not None else 0,
            },
        })
        results.append(result)
        return result

    def payload(**overrides) -> str:
        data = {
            "nome": "Auditoria Segura",
            "email": f"sec-{run_id}-general@example.com",
            "senha": "S3nha!audit",
        }
        data.update(overrides)
        return json.dumps(data, ensure_ascii=False)

    try:
        # A — referência e cabeçalhos
        add("A1", "configuracao", "Health público", "GET", "/solar/health")
        add("A2", "erro", "Rota inexistente", "GET", "/nao-existe")
        add(
            "A3", "configuracao", "Preflight CORS", "OPTIONS",
            "/solar/health",
            headers={
                "Origin": "https://origem.exemplo",
                "Access-Control-Request-Method": "GET",
            },
        )
        add("A4", "metodo", "Método não permitido", "PUT", "/solar/health")

        # B — criação válida e verificação de resposta/banco
        base_email = f"sec-{run_id}-base@example.com"
        valid = add(
            "B1", "entrada", "Criação válida de referência", "POST",
            "/examples/users", payload(email=base_email),
        )

        # C — autenticação e autorização no caminho HTTP
        add(
            "C1", "autenticacao", "POST sem credencial", "POST",
            "/examples/users",
            payload(email=f"sec-{run_id}-noauth@example.com"),
        )
        add(
            "C2", "autenticacao", "POST com Bearer inválido", "POST",
            "/examples/users",
            payload(email=f"sec-{run_id}-badtoken@example.com"),
            headers={"Authorization": "Bearer token-invalido"},
        )
        add(
            "C3", "autorizacao", "Tentativa de leitura por identificador",
            "GET", "/examples/users/1",
        )

        # D — validação de entrada
        add("D1", "entrada", "Corpo vazio", "POST", "/examples/users", "{}")
        add(
            "D2", "entrada", "Campos em branco", "POST", "/examples/users",
            json.dumps({"nome": "   ", "email": "   ", "senha": "   "}),
        )
        add(
            "D3", "entrada", "Campos nulos", "POST", "/examples/users",
            json.dumps({"nome": None, "email": None, "senha": None}),
        )
        add(
            "D4", "entrada", "E-mail inválido", "POST", "/examples/users",
            payload(email="sem-arroba"),
        )
        add(
            "D5", "entrada", "E-mail duplicado", "POST", "/examples/users",
            payload(email=base_email),
        )
        add(
            "D6", "entrada", "JSON malformado", "POST", "/examples/users",
            "{",
        )
        add(
            "D7", "entrada", "JSON de tipo lista", "POST", "/examples/users",
            "[]",
        )
        add(
            "D8", "entrada", "Content-Type incorreto", "POST",
            "/examples/users", payload(email=f"sec-{run_id}-text@example.com"),
            headers={"Content-Type": "text/plain"},
        )
        add(
            "D9", "entrada", "Tipo numérico em senha", "POST",
            "/examples/users",
            payload(email=f"sec-{run_id}-typepass@example.com", senha=123),
        )
        add(
            "D10", "entrada", "Tipo numérico em e-mail", "POST",
            "/examples/users",
            payload(email=123, senha=FIXTURE_TEXT),
        )
        add(
            "D11", "entrada", "Senha curta", "POST", "/examples/users",
            payload(email=f"sec-{run_id}-short@example.com", senha=FIXTURE_SHORT),
        )
        add(
            "D12", "entrada", "Nome muito longo (64 KiB)", "POST",
            "/examples/users",
            payload(
                email=f"sec-{run_id}-big@example.com",
                nome="A" * 65536,
            ),
            store_body=False,
        )

        # E — campos protegidos e injeção
        extra_email = f"sec-{run_id}-extra@example.com"
        add(
            "E1", "entrada", "Campos extras/protegidos", "POST",
            "/examples/users",
            payload(
                email=extra_email,
                id_user=999999,
                reset_password_user="true",
                data_created_user="1900-01-01T00:00:00",
            ),
        )
        sql_email = f"sec-{run_id}-sql@example.com"
        add(
            "E2", "entrada", "Payload de injeção SQL no nome", "POST",
            "/examples/users",
            payload(
                email=sql_email,
                nome="Robert'); DROP TABLE users;--",
            ),
        )
        add(
            "E3", "entrada", "Conteúdo HTML/script no nome", "POST",
            "/examples/users",
            payload(
                email=f"sec-{run_id}-xss@example.com",
                nome="<script>alert(1)</script>",
            ),
        )

        # F — repetição de tentativas inválidas (sem credenciais reais)
        for index in range(10):
            add(
                f"F{index + 1}", "protecao", "Tentativa inválida repetida",
                "POST", "/examples/users",
                payload(email=f"invalido-{run_id}-{index}"),
            )

        # G — verificação de banco e de resposta
        connection = db_connect(sqlite_path)
        try:
            rows = connection.execute(
                "SELECT id_user, name_user, email_user, password_user, "
                "reset_password_user, data_created_user "
                "FROM users WHERE email_user = ?",
                (base_email.lower(),),
            ).fetchall()
            extra = connection.execute(
                "SELECT id_user, reset_password_user, data_created_user "
                "FROM users WHERE email_user = ?",
                (extra_email.lower(),),
            ).fetchone()
            injected = connection.execute(
                "SELECT name_user FROM users WHERE email_user = ?",
                (sql_email.lower(),),
            ).fetchone()
            table_count = connection.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]
        finally:
            connection.close()

        db_evidence = {
            "base_row_count": len(rows),
            "base_id": rows[0][0] if rows else None,
            "base_name": rows[0][1] if rows else None,
            "base_email": rows[0][2] if rows else None,
            "password_is_plaintext": (
                rows[0][3] == "S3nha!audit" if rows else None
            ),
            "password_starts_bcrypt": (
                str(rows[0][3]).startswith("$2") if rows else None
            ),
            "extra_id": extra[0] if extra else None,
            "extra_reset_password": extra[1] if extra else None,
            "extra_created_at": extra[2] if extra else None,
            "injected_name": injected[0] if injected else None,
            "users_table_count": table_count,
        }

        output = {
            "run_id": run_id,
            "generated_at": utc_now(),
            "startup": startup,
            "environment": {
                "python": sys.version,
                "platform": __import__("platform").platform(),
            },
            "tests": results,
            "database": db_evidence,
            "notes": [
                "Dados sintéticos; nenhuma credencial real foi usada.",
                "Respostas 201 contêm apenas dados sintéticos criados pelo teste.",
                "O corpo de respostas 500/404 é registrado apenas como prévia.",
                "O teste não executa carga, exclusão ou migração.",
            ],
        }

        (WORKDIR / "RESULTADOS_TESTES.json").write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(json.dumps({
            "tests": len(results),
            "status_counts": {
                str(status): sum(
                    1 for item in results if item["status"] == status
                )
                for status in sorted({item["status"] for item in results})
            },
            "database": db_evidence,
            "output": str(WORKDIR / "RESULTADOS_TESTES.json"),
        }, ensure_ascii=False, indent=2))
        return 0

    finally:
        stop_server(process)


if __name__ == "__main__":
    raise SystemExit(main())
