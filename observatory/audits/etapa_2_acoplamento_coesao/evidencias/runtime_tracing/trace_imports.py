#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tracing de importações em runtime — Etapa 2 (auditoria complementar).

Este script é EXTERNO ao código da SOLAR. Ele não altera nenhum arquivo de
`nucleus/`, `orbits/`, `observatory/` ou `server.py`.

Mecanismos:
  1. `sys.addaudithook` no evento `import` — registra cada tentativa de
     importação, em ordem, antes de a aplicação ser importada;
  2. comparação de `sys.modules` antes/depois — registra o que foi
     efetivamente carregado (a auditoria vê tentativas; o diff vê sucesso).

Cenários (executados em processos separados, para não compartilhar
`sys.modules`):
  A. `verificador`      — executa `observatory.solar.cli.main(["check", ROOT])`
                          (o mesmo caminho de código de
                          `python -m observatory.solar check`), com o arquivo
                          de auditoria redirecionado para esta pasta.
  B. `bootstrap`        — importa `server` e executa `Kernel.mount()` com
                          SQLite em arquivo temporário, sem subir servidor.
  C. `modelo-isolado`   — importa `orbits.database.models.user_model` sem
                          inicializar `Database` (evidência da dependência
                          temporal).

Uso:
    py observatory/audits/etapa_2_acoplamento_coesao/evidencias/runtime_tracing/trace_imports.py --all
    py observatory/audits/etapa_2_acoplamento_coesao/evidencias/runtime_tracing/trace_imports.py --scenario bootstrap
    py observatory/audits/etapa_2_acoplamento_coesao/evidencias/runtime_tracing/trace_imports.py --compare

Saídas nesta pasta:
    imports_runtime_verificador.json
    imports_runtime_bootstrap.json
    imports_runtime_modelo_isolado.json
    comparacao_alcancabilidade.json
    verificador_stdout.txt
    check_audit/check-*.md
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import sysconfig
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TMP = HERE / "tmp"
SCENARIO_FILES = {
    "verificador": HERE / "imports_runtime_verificador.json",
    "bootstrap": HERE / "imports_runtime_bootstrap.json",
    "modelo-isolado": HERE / "imports_runtime_modelo_isolado.json",
}

# Alvos cuja ordem/contexto precisa ser registrada com pilha.
TARGETS = {
    "nucleus.database.database",
    "orbits.database.models",
    "orbits.database.models.user_model",
}

_events: list[dict] = []
_target_events: dict[str, list[dict]] = {}
_dynamic_calls: list[dict] = []
_seq = 0


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def sanitize(value: str) -> str:
    """Remove caminhos absolutos e normaliza carimbos de tempo do texto."""
    import re

    if not value:
        return value
    text = str(value).replace(str(ROOT), "<ROOT>")
    home = str(Path.home())
    if home and home != str(ROOT):
        text = text.replace(home, "<HOME>")
    text = re.sub(r"check-\d{4}-\d{2}-\d{2}-\d{6}-(correct|violation)\.md",
                  r"check-<TIMESTAMP>-\1.md", text)
    text = re.sub(r"\| gerado em \| [^|]+ \|", "| gerado em | <TIMESTAMP> |", text)
    return text


def rel_to_root(filename: str | None) -> str | None:
    if not filename:
        return None
    try:
        return Path(filename).resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return None


def project_stack(limit: int = 30) -> list[dict]:
    """Pilha sem textos de código e sem caminhos fora do projeto."""
    out: list[dict] = []
    frame = sys._getframe(1)
    while frame is not None and len(out) < limit:
        rel = rel_to_root(frame.f_code.co_filename)
        if rel:
            out.append({
                "file": rel,
                "line": frame.f_lineno,
                "function": frame.f_code.co_name,
            })
        frame = frame.f_back
    return out


def categorize(module: str) -> tuple[str, str | None]:
    """(categoria, origem) de um módulo em sys.modules."""
    obj = sys.modules.get(module)
    filename = getattr(obj, "__file__", None)
    if not filename:
        return "builtin", None

    path = Path(filename).resolve()
    rel = rel_to_root(str(path))
    if rel:
        if rel.startswith("reports/"):
            return "audit", rel
        if rel.startswith("tests/"):
            return "test", rel
        return "solar", rel

    parts = set(path.parts)
    if "site-packages" in parts or "dist-packages" in parts:
        return "external", module.split(".")[0]
    # Extensões C da instalação (DLLs/*.pyd) são biblioteca padrão, não
    # dependência externa.
    for base in (sys.base_prefix, sys.prefix):
        try:
            dlls = Path(base).resolve() / "DLLs"
            if dlls in path.parents:
                return "stdlib", None
        except OSError:
            pass
    try:
        stdlib = Path(sysconfig.get_paths()["stdlib"]).resolve()
        if stdlib in path.parents:
            return "stdlib", None
    except (KeyError, OSError):
        pass
    if str(path).startswith(sys.prefix):
        return "external", module.split(".")[0]
    return "other", None


def hook(event: str, args: tuple) -> None:
    """Audit hook: registra tentativas de importação em ordem."""
    global _seq
    if event != "import":
        return
    module = args[0]
    _seq += 1
    record = {"seq": _seq, "module": module}
    if module in TARGETS:
        record["database_loaded_at_event"] = "nucleus.database.database" in sys.modules
        record["user_model_loaded_at_event"] = (
            "orbits.database.models.user_model" in sys.modules
        )
        database_module = sys.modules.get("nucleus.database.database")
        database_class = getattr(database_module, "Database", None)
        record["database_orm_published_at_event"] = (
            getattr(database_class, "orm", None) is not None
        )
        record["stack"] = project_stack()
        _target_events.setdefault(module, []).append(record)
    _events.append(record)


def environment() -> dict:
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "system": platform.system(),
        "release": platform.release(),
        "root": "<ROOT>",
    }


def first_sequences() -> dict[str, int]:
    out: dict[str, int] = {}
    for event in _events:
        out.setdefault(event["module"], event["seq"])
    # `importlib.import_module` NÃO dispara o evento de auditoria `import`
    # (verificado em teste controlado). A ordem dessas chamadas vem do wrapper.
    for call in _dynamic_calls:
        if call.get("loaded"):
            out.setdefault(call["module"], call["seq"])
    return out


def install_dynamic_tracer() -> None:
    """Instrumenta importlib.import_module sem alterar a SOLAR.

    O evento de auditoria `import` é emitido pelo `__import__` embutido;
    `importlib.import_module` não o emite. Sem este wrapper, a importação
    dinâmica de Models ficaria invisível para o hook (e só apareceria no
    diff de `sys.modules`, sem ordem nem causalidade).
    """
    import importlib

    original = importlib.import_module

    def traced(name, package=None):
        global _seq
        _seq += 1
        database_module = sys.modules.get("nucleus.database.database")
        database_class = getattr(database_module, "Database", None)
        record = {
            "seq": _seq,
            "module": name,
            "caller_stack": project_stack(limit=20),
            "database_loaded_at_call": database_module is not None,
            "database_orm_published_at_call": (
                getattr(database_class, "orm", None) is not None
            ),
        }
        try:
            loaded = original(name, package)
            record["loaded"] = True
            record["loaded_module"] = getattr(loaded, "__name__", name)
            return loaded
        except BaseException as exc:
            record["loaded"] = False
            record["exception"] = type(exc).__name__
            raise
        finally:
            _dynamic_calls.append(record)

    importlib.import_module = traced


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------

def scenario_verificador() -> dict:
    import contextlib
    import io

    from observatory.solar import audit, cli

    audit_dir = HERE / "check_audit"
    if audit_dir.exists():
        for old in audit_dir.glob("*.md"):
            old.unlink()
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Redireciona SOMENTE o arquivo de auditoria do comando. O caminho de
    # código (CLI -> run_check -> ProjectValidator -> audit.record) é o mesmo.
    audit.audit_directory = lambda root: audit_dir

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exit_code = cli.main(["check", str(ROOT)])

    text = sanitize(buffer.getvalue())
    (HERE / "verificador_stdout.txt").write_text(text, encoding="utf-8")

    written = sorted(audit_dir.glob("check-*.md"))
    for path in written:
        body = sanitize(path.read_text(encoding="utf-8"))
        path.write_text(body, encoding="utf-8")

    return {
        "exit_code": exit_code,
        "audit_files_written": len(written),
        "stdout_file": "verificador_stdout.txt",
        "redirection": ("audit.audit_directory apontado para runtime_tracing/check_audit; "
                        "nenhum arquivo foi escrito em observatory/solar/check"),
    }


def scenario_bootstrap() -> dict:
    import shutil

    import server  # noqa: F401  (carrega o ponto de entrada, sem executar run())
    import nucleus.kernel as kernel_module

    TMP.mkdir(parents=True, exist_ok=True)
    env_file = TMP / "trace.env"
    env_file.write_text("", encoding="utf-8")
    db_file = TMP / "solar_trace.db"
    for candidate in (db_file, db_file.with_suffix(".db-journal")):
        if candidate.exists():
            candidate.unlink()
    storage = TMP / "storage_trace"
    shutil.rmtree(storage, ignore_errors=True)

    config = {
        "APP_ENV": "TEST",
        "DB_CONNECTION": "sqlite",
        "DB_NAME": db_file.as_posix(),
        "DB_HOST": None,
        "DB_PORT": None,
        "DB_USER": None,
        "DB_PASS": None,
        "CORS": None,
        "PORT": None,
        "HOST": None,
    }

    result = {
        "mount_ok": False,
        "config": {"APP_ENV": "TEST", "DB_CONNECTION": "sqlite",
                   "DB_NAME": "arquivo temporário em runtime_tracing/tmp"},
        "server_run_called": False,
    }

    kernel = None
    try:
        kernel = kernel_module.Kernel(
            env_file=str(env_file),
            config=config,
            storage_root=str(storage),
        )
        app = kernel.mount()
        result["mount_ok"] = True
        result["url_rules"] = len(list(app.url_map.iter_rules()))
        result["blueprints"] = sorted(app.blueprints)
        result["database"] = {
            "orm_published": kernel_module.Database.orm is not None,
            "model_published": kernel_module.Database.model is not None,
        }
    except Exception as exc:  # falha registrada, sem detalhes internos
        result["exception"] = type(exc).__name__
    finally:
        if kernel is not None:
            try:
                kernel.shutdown()
            except Exception:
                pass
        for candidate in (db_file, db_file.with_suffix(".db-journal"), env_file):
            try:
                candidate.unlink()
            except OSError:
                pass
        shutil.rmtree(storage, ignore_errors=True)

    return result


def scenario_modelo_isolado() -> dict:
    result = {"import_ok": False}
    try:
        import orbits.database.models.user_model as user_model  # noqa: F401
        result["import_ok"] = True
        result["module"] = user_model.__name__
    except Exception as exc:
        # Só o TIPO é registrado; a mensagem pode conter detalhes internos.
        result["exception"] = type(exc).__name__
    return result


SCENARIOS = {
    "verificador": scenario_verificador,
    "bootstrap": scenario_bootstrap,
    "modelo-isolado": scenario_modelo_isolado,
}


# --------------------------------------------------------------------------
# Execução de um cenário
# --------------------------------------------------------------------------

def run_scenario(name: str) -> int:
    baseline = set(sys.modules)
    install_dynamic_tracer()        # importlib.import_module não emite audit event
    sys.addaudithook(hook)          # antes de importar qualquer módulo da SOLAR
    outcome: dict = {}
    failures: list[dict] = []
    try:
        outcome = SCENARIOS[name]()
    except Exception as exc:
        failures.append({"stage": "scenario", "exception": type(exc).__name__})

    # Snapshot das CHAVES antes de categorizar: categorizar pode tocar em
    # `sys.modules` indiretamente (imports preguiçosos de bibliotecas).
    loaded_names = list(sys.modules)
    after: dict[str, tuple[str, str | None]] = {}
    for mod in loaded_names:
        try:
            after[mod] = categorize(mod)
        except Exception:
            after[mod] = ("other", None)
    loaded = sorted(set(after) - baseline)
    sequences = first_sequences()

    modules = []
    counts = {"solar": 0, "external": 0, "stdlib": 0, "builtin": 0,
              "audit": 0, "test": 0, "other": 0}
    for mod in loaded:
        category, origin = after[mod]
        counts[category] = counts.get(category, 0) + 1
        modules.append({
            "module": mod,
            "category": category,
            "origin": origin,
            "first_import_seq": sequences.get(mod),
        })

    solar = [m for m in modules if m["category"] == "solar"]
    attempted_solar = sorted({
        e["module"] for e in _events
        if e["module"].startswith(("nucleus", "orbits", "observatory", "server"))
    })
    not_loaded = [m for m in attempted_solar if m not in sys.modules]

    payload = {
        "scenario": name,
        "command": f"py observatory/audits/etapa_2_acoplamento_coesao/evidencias/runtime_tracing/trace_imports.py --scenario {name}",
        "environment": environment(),
        "instrumentation": {
            "mechanism": [
                "sys.addaudithook('import')",
                "monkeypatch importlib.import_module",
                "sys.modules diff",
            ],
            "hook_installed_before_scenario_import": True,
            "audit_hook_does_not_observe_importlib": True,
            "events_observed": len(_events),
        },
        "result": outcome,
        "counts": counts,
        "solar_modules": solar,
        "external_packages": sorted({m["origin"] for m in modules
                                     if m["category"] == "external" and m["origin"]}),
        "solar_import_attempts_not_loaded": not_loaded,
        "target_events": _target_events,
        "dynamic_import_calls": _dynamic_calls,
        "failures": failures,
    }

    path = SCENARIO_FILES[name]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
                    encoding="utf-8")
    print(f"[{name}] ok; módulos SOLAR={counts['solar']}; arquivo={path.name}")
    return 0


# --------------------------------------------------------------------------
# Comparação com a análise estática
# --------------------------------------------------------------------------

def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict]:
    import csv

    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def module_path(module: str) -> Path:
    base = ROOT / module.replace(".", "/")
    if (base / "__init__.py").exists():
        return base / "__init__.py"
    return base.with_suffix(".py")


def has_code(module: str) -> bool:
    import ast

    path = module_path(module)
    if not path.exists():
        return False
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
        for node in tree.body
    )


def is_package_init(module: str) -> bool:
    return module_path(module).name == "__init__.py"


def static_bfs(rows: list[dict], roots: list[str]) -> set[str]:
    from collections import defaultdict, deque

    graph: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        graph[row["source"]].add(row["target"])
    seen = set(roots)
    queue = deque(seen)
    while queue:
        node = queue.popleft()
        for nxt in graph.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def build_comparison() -> int:
    analysis = ROOT / "observatory" / "audits" / "etapa_2_acoplamento_coesao" / "dados"
    reach = load_json(analysis / "alcancabilidade.json") or {}
    metrics = read_csv_rows(analysis / "modulos_metricas.csv")
    dependencies = read_csv_rows(analysis / "dependencias_internas.csv")
    all_prod = {r["module"] for r in metrics}
    entry_points = reach.get("entry_points") or ["server", "observatory.solar.__main__"]

    # BFS recalculado a partir do MESMO grafo publicado — o artefato
    # `alcancabilidade.json` guarda apenas os não alcançáveis COM CÓDIGO,
    # não o conjunto alcançável completo.
    reachable = static_bfs(dependencies, entry_points) & all_prod
    unreachable = all_prod - reachable
    unreachable_with_code = {m for m in unreachable if has_code(m)}

    dynamic_targets = {
        r["target"] for r in dependencies if "dynamic" in r.get("kinds", "")
    }

    scenarios = {}
    union: set[str] = set()
    for name, path in SCENARIO_FILES.items():
        data = load_json(path)
        if data is None:
            scenarios[name] = {"executed": False}
            continue
        observed = {m["module"] for m in data["solar_modules"]}
        union |= observed
        unexpected = sorted(observed - reachable)
        reasons = {}
        for module in unexpected:
            if module in dynamic_targets:
                reasons[module] = "import_dinamico_modelado"
            elif is_package_init(module) and any(
                    other != module and other.startswith(module + ".")
                    for other in observed):
                reasons[module] = "import_implicito_de_pacote_pai"
            else:
                reasons[module] = "nao_explicado"
        scenarios[name] = {
            "executed": True,
            "solar_modules_observed": len(observed),
            "observed_in_reachable": len(observed & reachable),
            "unreachable_observed": sorted(observed & unreachable_with_code),
            "unexpected_modules": unexpected,
            "unexpected_classification": reasons,
            "result": data.get("result"),
            "counts": data.get("counts"),
        }

    not_observed = sorted(reachable - union)
    missing_reasons = {}
    for module in not_observed:
        if module in entry_points:
            missing_reasons[module] = "ponto_de_entrada_nao_executado"
        elif is_package_init(module):
            missing_reasons[module] = "pacote_pai_de_modulo_nao_executado"
        else:
            missing_reasons[module] = "aresta_estatica_nao_exercitada"

    comparison = {
        "reference": {
            "production_modules": len(all_prod),
            "production_modules_with_code": sum(1 for m in all_prod if has_code(m)),
            "reachable_modules_static": len(reachable),
            "reachable_modules_static_with_code": sum(1 for m in reachable if has_code(m)),
            "unreachable_modules_static": len(unreachable),
            "unreachable_modules_static_with_code": len(unreachable_with_code),
            "entry_points": entry_points,
            "dynamic_targets_modeled": sorted(dynamic_targets),
        },
        "scenarios": scenarios,
        "union": {
            "solar_modules_observed": len(union),
            "solar_modules_observed_with_code": sum(1 for m in union if has_code(m)),
            "observed_solar_modules": sorted(union),
            "reachable_not_observed": not_observed,
            "reachable_not_observed_reasons": missing_reasons,
            "unreachable_observed": sorted(union & unreachable_with_code),
            "unexpected_modules": sorted(union - reachable),
            "unexpected_classification": {
                m: ("import_dinamico_modelado" if m in dynamic_targets
                    else "import_implicito_de_pacote_pai" if is_package_init(m)
                    and any(o != m and o.startswith(m + ".") for o in union)
                    else "nao_explicado")
                for m in sorted(union - reachable)
            },
        },
        "static_unreachable_confirmed_absent_in_scenarios": sorted(
            unreachable_with_code - union),
        "previous_15_refuted_by_runtime": sorted(
            {item["module"] for item in reach.get("nao_alcancaveis_com_codigo", [])}
            & union),
        "notes": [
            "A ausência de um módulo em um cenário não prova ausência de uso em outras execuções.",
            "O cenário 'verificador' não exercita rotas/middlewares; o 'bootstrap' não serve requisições.",
            "Pacotes-pai são carregados implicitamente pelo Python ao importar um submódulo;",
            "o grafo estático não materializa essa aresta, por isso há módulos observados fora do BFS.",
        ],
    }
    out = HERE / "comparacao_alcancabilidade.json"
    out.write_text(json.dumps(comparison, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[compare] arquivo={out.name}; observados={len(union)}; "
          f"não observados={len(not_observed)}; "
          f"não alcançáveis ausentes={len(unreachable_with_code - union)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Tracing de importações SOLAR")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()

    if args.all:
        for name in ("verificador", "bootstrap", "modelo-isolado"):
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--scenario", name],
                cwd=str(ROOT),
            )
            if proc.returncode != 0:
                print(f"[{name}] falhou com código {proc.returncode}", file=sys.stderr)
        return build_comparison()

    if args.compare:
        return build_comparison()

    if args.scenario:
        return run_scenario(args.scenario)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
