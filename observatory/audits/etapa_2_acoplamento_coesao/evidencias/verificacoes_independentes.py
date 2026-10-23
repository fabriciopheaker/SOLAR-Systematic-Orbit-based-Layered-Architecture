#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoria final — verificações independentes das Etapas 2 e 3.

Este script NÃO importa `observatory/audits/etapa_2_acoplamento_coesao/scripts/solar_metrics.py`. Ele recalcula
um subconjunto das métricas com implementação própria e compara com os
artefatos publicados, para detectar erro sistemático no script original.

Verificações:
  V1  contagem de módulos e classes (produção)
  V2  CC por função/método (API do Radon) x `funcoes_complexidade.csv`
  V3  Halstead: funções com N1=N2=0 e volume por módulo
  V4  MI: módulos em 100 e causa (V=0 ou LLOC=0)
  V5  LCOM1/LCOM4 independentes x `coesao_classes.csv`
  V6  CBO independente do `Kernel` x `classes_cbo.csv`
  V7  acoplamento (Ca/Ce) de 4 módulos por resolvedor independente
  V8  complexidade cognitiva (execução do flake8) x CSV
  V9  evidência do ciclo dinâmico (linhas e chamadas no código)

Saída: `observatory/audits/etapa_2_acoplamento_coesao/evidencias/verificacoes.json`
Uso:   py observatory/audits/etapa_2_acoplamento_coesao/evidencias/verificacoes_independentes.py
"""

from __future__ import annotations

import ast
import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
ANALYSIS = HERE.parents[1] / "dados"
COMPLEXITY = HERE.parents[2] / "etapa_3_complexidade" / "dados"
OUT = HERE.parent
SKIP_ROOT = {"tests", "docs", "docker", "reports", "htmlcov", "storage", ".git",
             "__pycache__", ".pytest_cache"}


def production_files() -> list[Path]:
    out = []
    for p in sorted(ROOT.rglob("*.py")):
        rel = p.relative_to(ROOT)
        if "__pycache__" in rel.parts or rel.parts[0] in SKIP_ROOT:
            continue
        if rel.parts[:2] in (("observatory", "audits"), ("observatory", "tests")):
            continue
        out.append(p)
    return out


def module_of(p: Path) -> str:
    rel = p.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def read_csv(name: str) -> list[dict]:
    with (ANALYSIS / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def read_complexity(name: str) -> list[dict]:
    with (COMPLEXITY / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------- V2/V3/V4
def radon_checks(files: list[Path]) -> dict:
    from radon.complexity import cc_visit
    from radon.metrics import analyze, h_visit, mi_parameters

    per_module: dict[str, dict] = {}
    hal_zero = hal_funcs = 0
    mi100 = []
    for p in files:
        src = p.read_text(encoding="utf-8")
        mod = module_of(p)
        blocks = cc_visit(src)
        funcs = []
        for b in blocks:
            if b.__class__.__name__ == "Class":
                funcs.extend(b.methods)
            elif not getattr(b, "classname", None):
                funcs.append(b)
        per_module[mod] = {
            "functions": len(funcs),
            "cc_sum": sum(f.complexity for f in funcs),
            "cc_max": max((f.complexity for f in funcs), default=0),
            "max_length": max((f.endline - f.lineno + 1 for f in funcs), default=0),
        }

        h = h_visit(src)
        hal_funcs += len(h.functions)
        hal_zero += sum(1 for _, r in h.functions if r.N1 + r.N2 == 0)

        volume, _cc, lloc, _comments = mi_parameters(src)
        if volume <= 0 or lloc <= 0:
            mi100.append({"module": mod, "volume": volume, "lloc": lloc})
    return {
        "modules": len(files),
        "functions": sum(v["functions"] for v in per_module.values()),
        "cc_sum": sum(v["cc_sum"] for v in per_module.values()),
        "cc_max": max(v["cc_max"] for v in per_module.values()),
        "max_function_length": max(v["max_length"] for v in per_module.values()),
        "halstead_functions": hal_funcs,
        "halstead_zero": hal_zero,
        "halstead_zero_ratio": round(hal_zero / hal_funcs, 4) if hal_funcs else None,
        "mi_100_causes": mi100,
        "per_module": per_module,
    }


# --------------------------------------------------------------------- V5
def lcom_independent(files: list[Path]) -> dict:
    """LCOM1 e LCOM4 com implementação própria, só atributos de instância."""
    result = {}
    for p in files:
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            qual = f"{module_of(p)}.{node.name}"
            attrs: set[str] = set()
            methods: dict[str, set[str]] = {}
            calls: dict[str, set[str]] = {}
            # 1ª passada: TODOS os métodos de instância definem atributos
            # (inclusive __init__); depois os dunders saem da lista de métodos.
            for stmt in node.body:
                if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                decs = {getattr(d, "id", getattr(d, "attr", "")) for d in stmt.decorator_list}
                if "staticmethod" in decs or "classmethod" in decs or "property" in decs:
                    continue
                args = stmt.args.posonlyargs + stmt.args.args
                if not args:
                    continue
                me = args[0].arg
                used = set()
                called = set()
                for sub in ast.walk(stmt):
                    if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) \
                            and sub.value.id == me:
                        used.add(sub.attr)
                        if isinstance(sub.ctx, ast.Store):
                            attrs.add(sub.attr)
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                            and isinstance(sub.func.value, ast.Name) and sub.func.value.id == me:
                        called.add(sub.func.attr)
                if stmt.name.startswith("__") and stmt.name.endswith("__"):
                    continue
                methods[stmt.name] = used
                calls[stmt.name] = called
            if len(methods) < 2 or not attrs:
                continue
            names = list(methods)
            pairs = [(i, j) for i in range(len(names)) for j in range(i + 1, len(names))]
            q = sum(1 for i, j in pairs
                    if methods[names[i]] & methods[names[j]] & attrs)
            lcom1 = max((len(pairs) - q) - q, 0)

            parent = list(range(len(names)))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            def union(a, b):
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[rb] = ra

            for i, j in pairs:
                if methods[names[i]] & methods[names[j]] & attrs:
                    union(i, j)
            idx = {n: i for i, n in enumerate(names)}
            for i, n in enumerate(names):
                for c in calls[n]:
                    if c in idx:
                        union(i, idx[c])
            lcom4 = len({find(i) for i in range(len(names))})
            result[qual] = {"lcom1": lcom1, "lcom4": lcom4,
                            "attrs": len(attrs), "methods": len(methods)}
    return result


# --------------------------------------------------------------------- V6
def cbo_for(files: list[Path], qualnames: list[str]) -> dict:
    """CBO independente: classes internas referenciadas no corpo da classe."""
    classes: dict[str, set[str]] = {}
    for p in files:
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.ClassDef):
                classes.setdefault(n.name, set()).add(f"{module_of(p)}.{n.name}")
    all_classes = {x for s in classes.values() for x in s}

    result = {}
    for qual in qualnames:
        module, cname = qual.rsplit(".", 1)
        path = ROOT / (module.replace(".", "/") + ".py")
        if not path.exists():
            path = ROOT / module.replace(".", "/") / "__init__.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        local_module = {}
        for n in tree.body:
            if isinstance(n, ast.ImportFrom) and n.module \
                    and n.module.startswith(("nucleus", "orbits", "observatory")):
                for a in n.names:
                    local_module[a.asname or a.name] = f"{n.module}.{a.name}"
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cname)
        targets = set()
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Name):
                continue
            q = local_module.get(sub.id)
            if q in all_classes:
                targets.add(q)
            elif sub.id in classes and len(classes[sub.id]) == 1 \
                    and sub.id != cname:
                targets.add(next(iter(classes[sub.id])))
        targets.discard(qual)
        result[qual] = sorted(targets)
    return result


# --------------------------------------------------------------------- V7
def coupling_spotcheck(files: list[Path], modules: list[str]) -> dict:
    internal = {module_of(p) for p in files}
    wanted = {module_of(p): p for p in files if module_of(p) in modules}
    result = {}
    for mod, path in wanted.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        eferente = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    parts = a.name.split(".")
                    for i in range(len(parts), 0, -1):
                        cand = ".".join(parts[:i])
                        if cand in internal:
                            eferente.add(cand)
                            break
            elif isinstance(n, ast.ImportFrom):
                base = n.module or ""
                if n.level:
                    pkg = mod.split(".") if path.name == "__init__.py" else mod.split(".")[:-1]
                    up = n.level - 1
                    if up:
                        pkg = pkg[:-up] if up <= len(pkg) else []
                    base = ".".join(pkg + ([base] if base else []))
                for a in n.names:
                    cand = f"{base}.{a.name}" if base else a.name
                    if cand in internal:
                        eferente.add(cand)
                    elif base in internal:
                        eferente.add(base)
        result[mod] = {"Ce": len(eferente), "targets": sorted(eferente)}
    return result


# --------------------------------------------------------------------- V8
def cognitive(files: list[Path]) -> dict:
    cmd = [sys.executable, "-m", "flake8", "--select=CCR",
           "--max-cognitive-complexity=0",
           "--format=%(path)s|%(row)d|%(col)d|%(text)s",
           "nucleus", "orbits", "observatory/solar", "observatory/log", "server.py"]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=900)
    rows = []
    for line in proc.stdout.splitlines():
        parts = line.split("|")
        if len(parts) != 4:
            continue
        m = re.search(r"\((\d+) > 0\)", parts[3])
        if m:
            rows.append({"path": parts[0].replace("\\", "/"), "lineno": int(parts[1]),
                         "score": int(m.group(1))})
    return {"count": len(rows), "sum": sum(r["score"] for r in rows),
            "max": max((r["score"] for r in rows), default=0),
            "top": sorted(rows, key=lambda r: (-r["score"], r["path"]))[:5]}


def main() -> int:
    files = production_files()
    modules = [module_of(p) for p in files]
    radon = radon_checks(files)

    # V1
    v1 = {"production_files": len(files),
          "classes_ast": sum(1 for p in files
                             for n in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
                             if isinstance(n, ast.ClassDef))}

    # V2/V3/V4 contra CSVs
    funcs_csv = [r for r in read_complexity("funcoes_complexidade.csv") if r["layer"] != "Tests"]
    v2 = {
        "independent_functions": radon["functions"],
        "csv_functions": len(funcs_csv),
        "independent_cc_sum": radon["cc_sum"],
        "csv_cc_sum": sum(int(r["complexity"]) for r in funcs_csv),
        "independent_cc_max": radon["cc_max"],
        "csv_cc_max": max(int(r["complexity"]) for r in funcs_csv),
        "independent_max_length": radon["max_function_length"],
        "csv_max_length": max(int(r["length"]) for r in funcs_csv),
    }
    hal_csv = read_complexity("radon_halstead_modulos.csv")
    hal_prod = [r for r in hal_csv if r["layer"] != "Tests"]
    v3 = {
        "independent_zero": radon["halstead_zero"],
        "independent_functions": radon["halstead_functions"],
        "independent_ratio": radon["halstead_zero_ratio"],
        "csv_zero_production": sum(int(r["functions_zero_halstead"]) for r in hal_prod),
        "csv_functions_production": sum(int(r["functions"]) for r in hal_prod),
        "csv_volume_production": round(sum(float(r["volume"]) for r in hal_prod), 3),
        "modules_function_diff": [
            {"module": r["module"],
             "csv": int(r["functions"]),
             "independent": radon["per_module"].get(r["module"], {}).get("functions", 0)}
            for r in hal_prod
            if int(r["functions"]) != radon["per_module"].get(r["module"], {}).get("functions", 0)
        ],
    }
    v4 = {"modules_with_mi_100_due_to_zero": len(radon["mi_100_causes"]),
          "examples": radon["mi_100_causes"][:10]}

    # V5
    lcom_ind = lcom_independent(files)
    coh = {r["class"]: r for r in read_csv("coesao_classes.csv")}
    diffs1, diffs4, compared = [], [], 0
    for q, v in lcom_ind.items():
        c = coh.get(q)
        if not c or c["applicability"] != "aplicavel":
            continue
        compared += 1
        if int(c["lcom1"]) != v["lcom1"]:
            diffs1.append({"class": q, "csv": int(c["lcom1"]), "ind": v["lcom1"]})
        if int(c["lcom4"]) != v["lcom4"]:
            diffs4.append({"class": q, "csv": int(c["lcom4"]), "ind": v["lcom4"]})
    v5 = {"classes_compared": compared, "lcom1_diffs": diffs1, "lcom4_diffs": diffs4,
          "note": "implementação independente usa APENAS atributos de instância + chamadas; o script original usa todos os acessos no LCOM4"}

    # V6
    top_quals = ["nucleus.kernel.Kernel",
                 "nucleus.middleware.request_pipeline.RequestPipeline",
                 "nucleus.rules.project_validator.ProjectValidator",
                 "nucleus.broadcast.broadcast.Broadcast",
                 "server.Server"]
    cbo_ind = cbo_for(files, top_quals)
    cbo_csv = {r["class"]: r for r in read_csv("classes_cbo.csv")}
    v6 = {q: {"independent_count": len(cbo_ind[q]),
              "csv_count": int(cbo_csv[q]["cbo_internal_max"]),
              "equal_sets": cbo_ind[q] == cbo_csv[q]["targets_internal"].split(";"),
              "independent_targets": cbo_ind[q]}
          for q in top_quals}

    # V7
    spot = coupling_spotcheck(files, ["nucleus.rules.project_validator", "nucleus.kernel",
                                      "nucleus.exceptions.solar_exception",
                                      "nucleus.database.database"])
    mods = {r["module"]: r for r in read_csv("modulos_acoplamento.csv")}
    v7 = {m: {"independent_Ce": d["Ce"], "csv_Ce": int(mods[m]["Ce"]),
              "equal": d["Ce"] == int(mods[m]["Ce"])} for m, d in spot.items()}

    # V8
    cog = cognitive(files)
    cog_csv = read_complexity("complexidade_cognitiva.csv")
    v8 = {"independent_count": cog["count"], "csv_count": len(cog_csv),
          "independent_sum": cog["sum"],
          "csv_sum": sum(int(r["cognitive"]) for r in cog_csv),
          "independent_max": cog["max"],
          "csv_max": max(int(r["cognitive"]) for r in cog_csv),
          "top": cog["top"]}

    # V9
    db = (ROOT / "nucleus" / "database" / "database.py").read_text(encoding="utf-8")
    model = (ROOT / "orbits" / "database" / "models" / "user_model.py").read_text(encoding="utf-8")
    v9 = {
        "database_imports_models_package": 'MODELS_PACKAGE = "orbits.database.models"' in db,
        "database_calls_import_module": "importlib.import_module" in db,
        "sync_calls_import_models": "_import_models()" in db,
        "init_calls_sync_when_flag": "if cls.SYNC_ON_START:" in db and "cls.sync()" in db,
        "model_imports_database": "from nucleus.database.database import Database" in model,
        "model_defines_class_from_orm": "class Users(Database.orm)" in model,
    }

    report = {"root": str(ROOT), "checks": {
        "V1_corpus": v1, "V2_cc": v2, "V3_halstead": v3, "V4_mi": v4,
        "V5_lcom": v5, "V6_cbo_kernel": v6, "V7_coupling": v7,
        "V8_cognitive": v8, "V9_cycle_evidence": v9,
    }}
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "verificacoes.json").open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print(json.dumps(report, indent=2, ensure_ascii=False)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
