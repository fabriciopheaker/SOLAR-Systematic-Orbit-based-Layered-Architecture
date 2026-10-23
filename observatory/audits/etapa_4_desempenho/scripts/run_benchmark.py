"""Executa a auditoria de desempenho da Etapa 4 em ambiente isolado.

- Sobe `bench_server.py` como processo separado, em 127.0.0.1.
- Usa SQLite temporário e dados sintéticos.
- Gera carga com `http.client` + threads (sem instalar ferramenta externa).
- Preserva amostras brutas em CSV e indicadores em JSON.
- Não altera código de produção.

Uso:
    py observatory/audits/etapa_4/run_benchmark.py
    py observatory/audits/etapa_4/run_benchmark.py --smoke
"""

from __future__ import annotations

import argparse
import csv
import ctypes
import http.client
import importlib.metadata
import json
import math
import os
import platform
import sqlite3
import statistics
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
DATA = HERE.parents[1] / "dados"
RAW = DATA / "RESULTADOS_BRUTOS"
TMP = DATA / "tmp"
SERVER = HERE.parent / "bench_server.py"

HOST = "127.0.0.1"
TIMEOUT_S = 10.0
MAX_CONCURRENCY_HEALTH = 16
MAX_CONCURRENCY_CREATE = 8
MAX_REQUESTS_HEALTH = 240
MAX_REQUESTS_CREATE = 20
STOP_ERROR_RATE = 0.20
STOP_P95_MS = 5000.0


# ---------------------------------------------------------------------------
# Monitor de CPU/memória do processo do servidor (Windows)
# ---------------------------------------------------------------------------

class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


class ProcessMonitor(threading.Thread):
    """Amostra CPU acumulada e working set do processo do servidor."""

    def __init__(self, pid: int, interval: float = 0.05):
        super().__init__(daemon=True)
        self.pid = pid
        self.interval = interval
        self.samples: list[dict] = []
        self._stop = threading.Event()
        self._handle = None
        self._kernel32 = None
        self._psapi = None
        self._available = sys.platform == "win32"

    def _open(self) -> bool:
        if not self._available:
            return False

        self._kernel32 = ctypes.windll.kernel32
        self._psapi = ctypes.windll.psapi

        # QUERY_LIMITED_INFORMATION | QUERY_INFORMATION | VM_READ
        access = 0x1000 | 0x0400 | 0x0010
        self._handle = self._kernel32.OpenProcess(access, False, self.pid)
        return bool(self._handle)

    def _sample(self) -> dict | None:
        if not self._handle:
            return None

        creation = ctypes.c_ulonglong()
        exit_time = ctypes.c_ulonglong()
        kernel = ctypes.c_ulonglong()
        user = ctypes.c_ulonglong()

        ok = self._kernel32.GetProcessTimes(
            self._handle,
            ctypes.byref(creation),
            ctypes.byref(exit_time),
            ctypes.byref(kernel),
            ctypes.byref(user),
        )
        if not ok:
            return None

        cpu_s = (kernel.value + user.value) / 10_000_000.0

        memory = PROCESS_MEMORY_COUNTERS()
        memory.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        mem_ok = self._psapi.GetProcessMemoryInfo(
            self._handle,
            ctypes.byref(memory),
            ctypes.sizeof(memory),
        )

        return {
            "t": time.perf_counter(),
            "cpu_s": cpu_s,
            "rss_mb": (
                memory.WorkingSetSize / (1024 * 1024)
                if mem_ok else None
            ),
        }

    def run(self) -> None:
        if not self._open():
            return

        while not self._stop.is_set():
            sample = self._sample()
            if sample is not None:
                self.samples.append(sample)
            self._stop.wait(self.interval)

        # Uma última amostra depois do fim da carga.
        sample = self._sample()
        if sample is not None:
            self.samples.append(sample)

    def stop(self) -> None:
        self._stop.set()
        self.join(timeout=2)
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def percentile(values: list[float], p: float) -> float | None:
    """Percentil nearest-rank."""
    if not values:
        return None
    ordered = sorted(values)
    k = max(0, math.ceil((p / 100.0) * len(ordered)) - 1)
    return rounded(ordered[k])


def rounded(value: float | None, digits: int = 3) -> float | None:
    return None if value is None else round(float(value), digits)


def stats(values: list[float]) -> dict:
    if not values:
        return {
            "n": 0, "min": None, "mean": None, "median": None,
            "p90": None, "p95": None, "p99": None, "max": None,
        }

    return {
        "n": len(values),
        "min": rounded(min(values)),
        "mean": rounded(statistics.mean(values)),
        "median": rounded(statistics.median(values)),
        "p90": percentile(values, 90),
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
        "max": rounded(max(values)),
    }


def read_versions() -> dict:
    packages = [
        "Flask", "Werkzeug", "SQLAlchemy", "alembic",
        "bcrypt", "python-dotenv", "pytest", "radon",
    ]
    versions = {"python": sys.version, "platform": platform.platform()}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def csv_write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fields = [
        "scenario", "kind", "concurrency", "worker", "seq",
        "status", "ok", "latency_ms", "error", "body_code", "body_preview", "bytes",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


# ---------------------------------------------------------------------------
# Cliente HTTP
# ---------------------------------------------------------------------------

def body_for(kind: str, seq: int, run_id: str) -> str | None:
    if kind == "health":
        return None

    if kind == "create":
        return json.dumps(
            {
                "nome": f"Bench {seq}",
                "email": f"bench-{run_id}-{seq}@example.com",
                "senha": "S3nha!bench",
            },
            ensure_ascii=False,
        )

    if kind == "duplicate":
        return json.dumps(
            {
                "nome": "Duplicado",
                "email": f"dup-{run_id}@example.com",
                "senha": "S3nha!bench",
            },
            ensure_ascii=False,
        )

    if kind == "invalid":
        return json.dumps(
            {
                "nome": "Invalido",
                "email": "sem-arroba",
                "senha": "S3nha!bench",
            },
            ensure_ascii=False,
        )

    raise ValueError(kind)


def expected_ok(kind: str, status: int, body_code: str | None) -> bool:
    if kind == "health":
        return status == 200 and body_code is None
    if kind == "create":
        return status == 201
    if kind == "duplicate":
        return status == 400 and body_code == "EMAIL_TAKEN"
    if kind == "invalid":
        return status == 400 and body_code == "INVALID_EMAIL"
    return False


def request_once(conn: http.client.HTTPConnection, kind: str, seq: int,
                 run_id: str, timeout: float) -> dict:
    body = body_for(kind, seq, run_id)
    headers = {"Content-Type": "application/json"} if body else {}
    path = "/solar/health" if kind == "health" else "/examples/users"
    method = "GET" if kind == "health" else "POST"

    started = time.perf_counter()
    try:
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        payload = response.read()
        latency_ms = (time.perf_counter() - started) * 1000

        body_code = None
        if payload:
            try:
                parsed = json.loads(payload)
                if isinstance(parsed, dict):
                    body_code = parsed.get("code")
            except json.JSONDecodeError:
                body_code = None

        ok = expected_ok(kind, response.status, body_code)

        return {
            "status": response.status,
            "ok": ok,
            "latency_ms": latency_ms,
            "error": None,
            "body_code": body_code,
            "body_preview": (
                None if ok
                else payload[:240].decode("utf-8", "replace")
            ),
            "bytes": len(payload),
        }
    except Exception as error:  # noqa: BLE001 - erro do gerador é dado
        latency_ms = (time.perf_counter() - started) * 1000
        return {
            "status": 0,
            "ok": False,
            "latency_ms": latency_ms,
            "error": type(error).__name__,
            "body_code": None,
            "body_preview": None,
            "bytes": 0,
        }


def run_load(
    host: str,
    port: int,
    kind: str,
    total: int,
    concurrency: int,
    run_id: str,
    scenario: str,
    timeout: float = TIMEOUT_S,
) -> tuple[list[dict], float, dict]:
    rows: list[dict] = []
    lock = threading.Lock()
    barrier = threading.Barrier(concurrency)

    def worker(worker_id: int) -> None:
        conn: http.client.HTTPConnection | None = None
        try:
            barrier.wait(timeout=10)
        except threading.BrokenBarrierError:
            return

        try:
            for seq in range(worker_id, total, concurrency):
                if conn is None:
                    conn = http.client.HTTPConnection(
                        host, port, timeout=timeout
                    )

                result = request_once(conn, kind, seq, run_id, timeout)
                result.update(
                    {
                        "scenario": scenario,
                        "kind": kind,
                        "concurrency": concurrency,
                        "worker": worker_id,
                        "seq": seq,
                    }
                )
                with lock:
                    rows.append(result)

                if result["error"]:
                    conn.close()
                    conn = None
        finally:
            if conn is not None:
                conn.close()

    threads = [
        threading.Thread(target=worker, args=(index,), daemon=True)
        for index in range(concurrency)
    ]

    started = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=timeout + 5)
    duration = time.perf_counter() - started

    return rows, duration, {}


def summarize(
    rows: list[dict],
    duration_s: float,
    monitor_samples: list[dict],
    scenario: str,
    kind: str,
    concurrency: int,
    total: int,
    started_at: str,
) -> dict:
    expected_latencies = [row["latency_ms"] for row in rows if row["ok"]]
    all_latencies = [row["latency_ms"] for row in rows]
    unexpected = [row for row in rows if not row["ok"]]
    transport_errors = [row for row in rows if row["error"]]
    status_counts: dict[str, int] = {}
    error_counts: dict[str, int] = {}

    for row in rows:
        status_key = str(row["status"])
        status_counts[status_key] = status_counts.get(status_key, 0) + 1
        if row["error"]:
            error_counts[row["error"]] = error_counts.get(row["error"], 0) + 1

    cpu_pct = None
    memory_mean = None
    memory_max = None
    if monitor_samples:
        usable = [sample for sample in monitor_samples if sample["cpu_s"] is not None]
        if len(usable) >= 2 and duration_s > 0:
            cpu_pct = rounded(
                ((usable[-1]["cpu_s"] - usable[0]["cpu_s"]) / duration_s) * 100,
                2,
            )
        memory_values = [
            sample["rss_mb"] for sample in monitor_samples
            if sample["rss_mb"] is not None
        ]
        if memory_values:
            memory_mean = rounded(statistics.mean(memory_values), 2)
            memory_max = rounded(max(memory_values), 2)

    return {
        "scenario": scenario,
        "kind": kind,
        "concurrency": concurrency,
        "total_requests": total,
        "completed": len(rows),
        "incomplete": max(0, total - len(rows)),
        "expected": len(expected_latencies),
        "unexpected": len(unexpected),
        "transport_errors": len(transport_errors),
        "error_rate": rounded(len(unexpected) / len(rows), 4) if rows else None,
        "status_counts": status_counts,
        "transport_error_types": error_counts,
        "duration_s": rounded(duration_s),
        "throughput_completed_rps": rounded(len(rows) / duration_s, 3) if duration_s else None,
        "throughput_expected_rps": rounded(len(expected_latencies) / duration_s, 3) if duration_s else None,
        "latency_expected_ms": stats(expected_latencies),
        "latency_all_ms": stats(all_latencies),
        "cpu_pct_single_core": cpu_pct,
        "memory_mb": {"mean": memory_mean, "max": memory_max},
        "started_at": started_at,
        "ended_at": now_utc(),
    }


# ---------------------------------------------------------------------------
# Ciclo principal
# ---------------------------------------------------------------------------

def start_server(workdir: Path) -> tuple[subprocess.Popen, dict, float]:
    RAW.mkdir(parents=True, exist_ok=True)
    (workdir / "tmp").mkdir(parents=True, exist_ok=True)

    ready_path = workdir / "startup.json"
    if ready_path.exists():
        ready_path.unlink()

    log_path = RAW / "server.log"
    log_file = log_path.open("w", encoding="utf-8")

    started = time.perf_counter()
    process = subprocess.Popen(
        [
            sys.executable,
            str(SERVER),
            "--workdir", str(workdir),
        ],
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.time() + 40
    ready = None
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Servidor encerrou antes de ficar pronto; veja {log_path}"
            )
        if ready_path.exists():
            try:
                ready = json.loads(ready_path.read_text(encoding="utf-8"))
                break
            except json.JSONDecodeError:
                pass
        time.sleep(0.05)

    if ready is None:
        process.terminate()
        raise TimeoutError("Servidor não ficou pronto em 40 s.")

    ready["time_to_ready_parent_ms"] = rounded(
        (time.perf_counter() - started) * 1000
    )
    return process, ready, (time.perf_counter() - started) * 1000


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


def seed_duplicate(host: str, port: int, run_id: str) -> None:
    conn = http.client.HTTPConnection(host, port, timeout=TIMEOUT_S)
    try:
        body = json.dumps(
            {
                "nome": "Duplicado",
                "email": f"dup-{run_id}@example.com",
                "senha": "S3nha!bench",
            },
            ensure_ascii=False,
        )
        conn.request(
            "POST",
            "/examples/users",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        response.read()
        if response.status != 201:
            raise RuntimeError(
                f"Seed de duplicado falhou: HTTP {response.status}"
            )
    finally:
        conn.close()


def check_health(host: str, port: int) -> dict:
    conn = http.client.HTTPConnection(host, port, timeout=TIMEOUT_S)
    try:
        conn.request("GET", "/solar/health")
        response = conn.getresponse()
        payload = response.read()
        return {
            "status": response.status,
            "body": json.loads(payload) if payload else None,
        }
    finally:
        conn.close()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


def database_info(sqlite_path: Path) -> dict:
    info = {
        "path": str(sqlite_path),
        "exists": sqlite_path.exists(),
        "size_bytes": sqlite_path.stat().st_size if sqlite_path.exists() else None,
        "user_count": None,
        "tables": [],
    }
    if not sqlite_path.exists():
        return info

    try:
        connection = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
        try:
            tables = [
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' ORDER BY name"
                )
            ]
            info["tables"] = tables
            if "users" in tables:
                info["user_count"] = connection.execute(
                    "SELECT COUNT(*) FROM users"
                ).fetchone()[0]
        finally:
            connection.close()
    except sqlite3.Error as error:
        info["error"] = f"{type(error).__name__}: {error}"

    return info


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)

    # Remove artefatos de execuções anteriores para não misturar
    # resultados de smoke com a medição completa.
    for pattern in ("*.csv", "*.json", "server.log"):
        for old in RAW.glob(pattern):
            old.unlink()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    workdir = DATA
    process, startup, time_to_ready = start_server(workdir)

    environment = {
        "run_id": run_id,
        "started_at": now_utc(),
        "command": " ".join([sys.executable, *sys.argv]),
        "cwd": str(ROOT),
        "versions": read_versions(),
        "limits": {
            "health_concurrency_max": MAX_CONCURRENCY_HEALTH,
            "create_concurrency_max": MAX_CONCURRENCY_CREATE,
            "health_requests_per_level": MAX_REQUESTS_HEALTH,
            "create_requests_per_level": MAX_REQUESTS_CREATE,
            "timeout_s": TIMEOUT_S,
        },
        "server": startup,
        "time_to_ready_parent_ms": rounded(time_to_ready),
    }
    write_json(RAW / "environment.json", environment)

    scenarios: list[dict] = []
    safety = {
        "aborted": False,
        "reason": None,
        "limits": {
            "max_error_rate": STOP_ERROR_RATE,
            "max_p95_ms": STOP_P95_MS,
        },
    }

    health = check_health(HOST, startup["port"])
    if health["status"] != 200 or not health["body"] or health["body"].get("status") != "ok":
        stop_server(process)
        raise RuntimeError(f"Verificação funcional falhou: {health}")

    seed_duplicate(HOST, startup["port"], run_id)

    # Aquecimento, fora das estatísticas.
    run_load(
        HOST, startup["port"], "health", 30, 1, run_id,
        "aquecimento_health",
    )
    run_load(
        HOST, startup["port"], "create", 1, 1, run_id + "-warmup",
        "aquecimento_create",
    )

    health_levels = [1, 1, 1, 2, 4, 8, 16]
    if args.smoke:
        health_levels = [1, 2]
        create_levels = [1]
    else:
        create_levels = [1, 2, 4, 8]

    for index, concurrency in enumerate(health_levels, start=1):
        if concurrency > MAX_CONCURRENCY_HEALTH:
            break
        scenario = (
            f"A_referencia_health_r{index}"
            if concurrency == 1
            else f"C_health_c{concurrency}"
        )
        if index == 4:
            scenario = "B_baixa_carga_health_c2"

        monitor = ProcessMonitor(startup["pid"])
        monitor.start()
        started_at = now_utc()
        rows, duration, _ = run_load(
            HOST, startup["port"], "health",
            MAX_REQUESTS_HEALTH, concurrency, run_id, scenario,
        )
        monitor.stop()

        summary = summarize(
            rows, duration, monitor.samples, scenario, "health",
            concurrency, MAX_REQUESTS_HEALTH, started_at,
        )
        scenarios.append(summary)
        csv_write(RAW / f"{scenario}.csv", rows)
        write_json(RAW / f"{scenario}.json", summary)

        if summary["error_rate"] and summary["error_rate"] > STOP_ERROR_RATE:
            safety.update(
                aborted=True,
                reason=f"{scenario}: error_rate={summary['error_rate']}",
            )
            break
        p95 = summary["latency_expected_ms"]["p95"]
        if p95 is not None and p95 > STOP_P95_MS:
            safety.update(
                aborted=True,
                reason=f"{scenario}: p95_ms={p95}",
            )
            break

    if not safety["aborted"]:
        for concurrency in create_levels:
            if concurrency > MAX_CONCURRENCY_CREATE:
                break
            scenario = f"C_create_c{concurrency}" if concurrency > 1 else "A_referencia_create_c1"

            monitor = ProcessMonitor(startup["pid"])
            monitor.start()
            started_at = now_utc()
            rows, duration, _ = run_load(
                HOST, startup["port"], "create",
                MAX_REQUESTS_CREATE, concurrency,
                f"{run_id}-{scenario}", scenario,
            )
            monitor.stop()

            summary = summarize(
                rows, duration, monitor.samples, scenario, "create",
                concurrency, MAX_REQUESTS_CREATE, started_at,
            )
            scenarios.append(summary)
            csv_write(RAW / f"{scenario}.csv", rows)
            write_json(RAW / f"{scenario}.json", summary)

            if summary["error_rate"] and summary["error_rate"] > STOP_ERROR_RATE:
                safety.update(
                    aborted=True,
                    reason=f"{scenario}: error_rate={summary['error_rate']}",
                )
                break
            p95 = summary["latency_expected_ms"]["p95"]
            if p95 is not None and p95 > STOP_P95_MS:
                safety.update(
                    aborted=True,
                    reason=f"{scenario}: p95_ms={p95}",
                )
                break

    if process.poll() is None:
        for kind, scenario, total in [
            ("duplicate", "E_persistencia_duplicate_c1", 60),
            ("invalid", "E_validacao_invalid_c1", 60),
        ]:
            monitor = ProcessMonitor(startup["pid"])
            monitor.start()
            started_at = now_utc()
            rows, duration, _ = run_load(
                HOST, startup["port"], kind, total, 1, run_id, scenario,
            )
            monitor.stop()

            summary = summarize(
                rows, duration, monitor.samples, scenario, kind,
                1, total, started_at,
            )
            scenarios.append(summary)
            csv_write(RAW / f"{scenario}.csv", rows)
            write_json(RAW / f"{scenario}.json", summary)

            if summary["error_rate"] and summary["error_rate"] > STOP_ERROR_RATE:
                safety.update(
                    aborted=True,
                    reason=f"{scenario}: error_rate={summary['error_rate']}",
                )
                break

    post_load_health = check_health(HOST, startup["port"])
    stop_server(process)

    sqlite_path = Path(startup["sqlite_path"])
    executed = {scenario["scenario"] for scenario in scenarios}
    planned = [
        "A_referencia_health_r1",
        "A_referencia_health_r2",
        "A_referencia_health_r3",
        "B_baixa_carga_health_c2",
        "C_health_c4",
        "C_health_c8",
        "C_health_c16",
        "A_referencia_create_c1",
        "C_create_c2",
        "C_create_c4",
        "C_create_c8",
        "E_persistencia_duplicate_c1",
        "E_validacao_invalid_c1",
    ]
    not_executed = [
        {
            "scenario": name,
            "reason": (
                safety["reason"]
                if safety["aborted"]
                else "não planejado para esta execução"
            ),
        }
        for name in planned
        if name not in executed
    ]

    consolidated = {
        "run_id": run_id,
        "generated_at": now_utc(),
        "environment": environment,
        "startup": startup,
        "time_to_ready_parent_ms": rounded(time_to_ready),
        "scenarios": scenarios,
        "safety": safety,
        "not_executed": not_executed,
        "post_load_health": post_load_health,
        "database": database_info(sqlite_path),
        "notes": [
            "Latência medida no cliente, incluindo loopback e primeira conexão de cada worker.",
            "Percentis nearest-rank; amostras pequenas tornam P99 instável.",
            "CPU em equivalente de um núcleo; pode passar de 100% em multithread.",
            "Aquecimento não entra nas estatísticas.",
            "Não houve comparação histórica nem segunda arquitetura.",
        ],
    }
    write_json(DATA / "RESULTADOS_CONSOLIDADOS.json", consolidated)

    print(json.dumps(
        {
            "scenarios": len(scenarios),
            "aborted": safety["aborted"],
            "database": consolidated["database"],
            "consolidated": str(DATA / "RESULTADOS_CONSOLIDADOS.json"),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
