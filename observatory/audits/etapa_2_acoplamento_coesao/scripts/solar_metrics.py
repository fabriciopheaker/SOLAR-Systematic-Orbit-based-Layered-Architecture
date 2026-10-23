#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLAR — recálculo das métricas estruturais não cobertas (ou mal cobertas)
pelos relatórios Radon preservados em ``etapa_3_complexidade/dados/radon``.

O que este script calcula (somente leitura sobre o código-fonte):

1. Grafo de dependências internas (AST), separando:
   - imports internos (produção)  -> métricas fan-in / fan-out / instabilidade
   - imports de testes            -> coluna separada (fan-in de teste)
   - imports externos / stdlib    -> NÃO entram nas métricas de acoplamento
   - imports condicionais/deferidos -> contados, mas sinalizados
2. Ca, Ce, I = Ce/(Ca+Ce), por módulo e por camada.
3. Componentes fortemente conexos (Tarjan) e ciclos.
4. CBO por classe (aproximação por AST; ver docstring de ``class_cbo``).
5. Coesão por classe: atributos de instância/classe, métodos, LCOM1 (CK),
   LCOM* (Henderson-Sellers), LCOM4 (Hitz-Montazeri), TCC, e
   aplicabilidade/inaplicabilidade de cada métrica.
6. Consolidação dos JSONs do Radon (cc / hal / mi / raw): agregação por
   módulo e por camada, comprimento de função, distribuição de ranks.

Uso:
    py observatory/audits/etapa_2_acoplamento_coesao/scripts/solar_metrics.py
    py observatory/audits/etapa_2_acoplamento_coesao/scripts/solar_metrics.py --root . --out observatory/audits/etapa_2_acoplamento_coesao/dados --out-complexity observatory/audits/etapa_3_complexidade/dados

Saídas de acoplamento/coesão (em ``--out``):
    modulos_acoplamento.csv
    dependencias_internas.csv
    dependencias_externas.csv
    classes_cbo.csv
    coesao_classes.csv
    ciclos_scc.json
    camadas_resumo.csv
    modulos_metricas.csv
    resumo_metricas.json

Saídas de complexidade (em ``--out-complexity``):
    funcoes_complexidade.csv
    complexidade_cognitiva.csv
    radon_halstead_modulos.csv
    validacao_radon.json

Nenhum arquivo do projeto é modificado.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", "htmlcov", "reports",
    "docs", "docker", "storage", "node_modules", ".venv", "venv",
}


# --------------------------------------------------------------------------
# Inventário de arquivos
# --------------------------------------------------------------------------

def module_name(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def is_package(path: Path) -> bool:
    return path.name == "__init__.py"


def iter_sources(root: Path) -> list[tuple[str, Path, bool]]:
    """(módulo, caminho, é_teste) para todos os .py do projeto.

    Apenas diretórios de PRIMEIRO NÍVEL listados em SKIP_DIRS são ignorados
    (ex.: a pasta de dados `storage/`), para não excluir pacotes internos
    homônimos como `nucleus/storage/`.
    """
    out: list[tuple[str, Path, bool]] = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if "__pycache__" in rel.parts or rel.parts[0] in SKIP_DIRS:
            continue
        # Ferramentas de auditoria do próprio Observatory não são
        # código de produção do corpus analisado.
        if rel.parts[:2] == ("observatory", "audits"):
            continue
        # A suíte de testes pode estar sob observatory/tests; ela
        # entra como corpus de teste, nunca como produção.
        if rel.parts[:2] == ("observatory", "tests"):
            mod = module_name(root, path)
            if mod:
                out.append((mod, path, True))
            continue
        mod = module_name(root, path)
        if not mod:
            continue
        out.append((mod, path, mod == "tests" or mod.startswith("tests.")))
    return out


def layer_of(module: str) -> str:
    if module == "tests" or module.startswith("tests."):
        return "Tests"
    if module.startswith("observatory.tests"):
        return "Tests"
    if module == "server":
        return "Bootstrap"
    if module.startswith("nucleus.") or module == "nucleus":
        return "Nucleus"
    if module.startswith("orbits.planets."):
        return "Orbits/Planets"
    if module.startswith("orbits.database"):
        return "Orbits/Database"
    if module.startswith("orbits.") or module == "orbits":
        return "Orbits"
    if module.startswith("observatory.") or module == "observatory":
        return "Observatory"
    return "Outros"


def sublayer_of(module: str) -> str:
    parts = module.split(".")
    if parts[0] == "nucleus" and len(parts) > 1:
        return "nucleus/" + parts[1]
    if parts[0] == "orbits" and len(parts) > 1:
        if parts[1] == "planets" and len(parts) > 2:
            return "orbits/planets/" + parts[2]
        return "orbits/" + parts[1]
    if parts[0] == "observatory":
        return "observatory/" + parts[1] if len(parts) > 1 else "observatory"
    return module


# --------------------------------------------------------------------------
# Grafo de imports
# --------------------------------------------------------------------------

@dataclass
class ImportRef:
    source: str
    target: str | None          # None => externo
    external: str | None
    lineno: int
    kind: str                   # "module" | "deferred" | "type_checking" | "protected"
    raw: str


class ImportCollector(ast.NodeVisitor):
    def __init__(self, module: str, package: bool, internal: set[str]):
        self.module = module
        self.is_pkg = package
        self.internal = internal
        self.refs: list[ImportRef] = []
        self.symbols: dict[str, tuple[str, str]] = {}   # local -> (kind, qualified)
        self._func_depth = 0
        self._type_checking = 0
        self._protected = 0

    # -- resolução ---------------------------------------------------
    def _absolute_module(self) -> str:
        parts = self.module.split(".")
        base = parts if self.is_pkg else parts[:-1]
        return ".".join(base)

    def _relative(self, level: int, target: str | None) -> str:
        base = self._absolute_module()
        parts = base.split(".") if base else []
        up = level - 1
        if up:
            parts = parts[:-up] if up <= len(parts) else []
        base = ".".join(parts)
        if target:
            return f"{base}.{target}" if base else target
        return base

    def _deepest_internal(self, dotted: str) -> str | None:
        parts = dotted.split(".")
        for i in range(len(parts), 0, -1):
            cand = ".".join(parts[:i])
            if cand in self.internal:
                return cand
        return None

    def _kind(self) -> str:
        if self._type_checking:
            return "type_checking"
        if self._func_depth:
            return "deferred"
        if self._protected:
            return "protected"
        return "module"

    def _add(self, target: str | None, external: str | None, node: ast.AST, raw: str):
        self.refs.append(ImportRef(
            source=self.module, target=target, external=external,
            lineno=getattr(node, "lineno", 0), kind=self._kind(), raw=raw,
        ))

    # -- visita ------------------------------------------------------
    def visit_If(self, node: ast.If):
        is_tc = False
        test = node.test
        if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
            is_tc = True
        elif isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
            is_tc = True
        if is_tc:
            self._type_checking += 1
            for stmt in node.body:
                self.visit(stmt)
            self._type_checking -= 1
            for stmt in node.orelse:
                self.visit(stmt)
            return
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        self._protected += 1
        self.generic_visit(node)
        self._protected -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._func_depth += 1
        self.generic_visit(node)
        self._func_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            target = self._deepest_internal(alias.name)
            external = None if target else alias.name.split(".")[0]
            self._add(target, external, node, f"import {alias.name}")
            local = alias.asname or alias.name.split(".")[0]
            if alias.asname:
                if target:
                    self.symbols[local] = ("module", target)
                else:
                    self.symbols[local] = ("external_module", alias.name)
            else:
                root_internal = self._deepest_internal(alias.name.split(".")[0])
                self.symbols[local] = (
                    ("module", root_internal) if root_internal
                    else ("external_module", alias.name.split(".")[0])
                )

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        absmod = self._relative(node.level, mod) if node.level else mod
        base_internal = self._deepest_internal(absmod)
        for alias in node.names:
            if alias.name == "*":
                continue
            candidate = f"{absmod}.{alias.name}" if absmod else alias.name
            cand_internal = candidate if candidate in self.internal else None
            target = cand_internal or base_internal
            external = None
            if target is None:
                external = absmod.split(".")[0] if absmod else None
            if target is None and not absmod:
                target = None
            self._add(target, external, node, f"from {absmod} import {alias.name}")
            local = alias.asname or alias.name
            if cand_internal:
                self.symbols[local] = ("module", cand_internal)
            elif base_internal:
                self.symbols[local] = ("symbol", f"{base_internal}.{alias.name}")
            else:
                self.symbols[local] = ("external_symbol", f"{absmod}.{alias.name}" if absmod else alias.name)


# --------------------------------------------------------------------------
# Tarjan (SCC) iterativo
# --------------------------------------------------------------------------

def strongly_connected_components(nodes: Iterable[str], edges: dict[str, set[str]]):
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    stack: list[str] = []
    result: list[list[str]] = []
    counter = 0

    for start in nodes:
        if start in index:
            continue
        work = [(start, 0)]
        while work:
            v, pi = work[-1]
            if pi == 0:
                index[v] = low[v] = counter
                counter += 1
                stack.append(v)
                on_stack[v] = True
            succ = sorted(edges.get(v, ()))
            if pi < len(succ):
                w = succ[pi]
                work[-1] = (v, pi + 1)
                if w not in index:
                    work.append((w, 0))
                elif on_stack.get(w):
                    low[v] = min(low[v], index[w])
            else:
                work.pop()
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[v])
                if low[v] == index[v]:
                    comp = []
                    while True:
                        w = stack.pop()
                        on_stack[w] = False
                        comp.append(w)
                        if w == v:
                            break
                    result.append(comp)
    return result


# --------------------------------------------------------------------------
# Classes: CBO e coesão
# --------------------------------------------------------------------------

@dataclass
class MethodInfo:
    name: str
    lineno: int
    endline: int
    kind: str                 # instance | class | static | property
    accesses: set[str] = field(default_factory=set)
    writes: set[str] = field(default_factory=set)
    calls: set[str] = field(default_factory=set)


@dataclass
class ClassInfo:
    module: str
    qualname: str
    name: str
    path: str
    lineno: int
    endline: int
    bases: list[str]
    instance_attrs: set[str] = field(default_factory=set)
    class_attrs: set[str] = field(default_factory=set)
    methods: list[MethodInfo] = field(default_factory=list)
    names: set[str] = field(default_factory=set)       # nomes simples usados
    dotted: set[str] = field(default_factory=set)      # cadeias a.b.c usadas
    cbo_internal_min: set[str] = field(default_factory=set)
    cbo_internal_max: set[str] = field(default_factory=set)
    cbo_external: set[str] = field(default_factory=set)
    cbo_ambiguous: set[str] = field(default_factory=set)


def decorator_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    out = set()
    for d in node.decorator_list:
        if isinstance(d, ast.Name):
            out.add(d.id)
        elif isinstance(d, ast.Attribute):
            out.add(d.attr)
        elif isinstance(d, ast.Call):
            f = d.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


def first_param(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    args = node.args.posonlyargs + node.args.args
    return args[0].arg if args else None


def dotted_name(node: ast.AST) -> str | None:
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def collect_class(module: str, path: str, node: ast.ClassDef, prefix: str = "") -> list[ClassInfo]:
    qual = f"{prefix}{node.name}"
    info = ClassInfo(
        module=module, qualname=f"{module}.{qual}",
        name=node.name, path=path,
        lineno=node.lineno, endline=getattr(node, "endline", node.lineno),
        bases=[dotted_name(b) or getattr(b, "id", "") for b in node.bases],
    )
    classes = [info]

    for stmt in node.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decs = decorator_names(stmt)
            if "staticmethod" in decs:
                kind = "static"
            elif "classmethod" in decs:
                kind = "class"
            elif "property" in decs or any(d in decs for d in ("setter", "getter", "deleter")):
                kind = "property"
            else:
                kind = "instance"
            m = MethodInfo(name=stmt.name, lineno=stmt.lineno,
                           endline=getattr(stmt, "endline", stmt.lineno), kind=kind)
            receiver = "cls" if kind == "class" else ("self" if kind == "instance" else None)
            p = first_param(stmt)
            if kind in ("instance", "class") and p:
                receiver = p
            for sub in ast.walk(stmt):
                if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) \
                        and receiver and sub.value.id == receiver:
                    m.accesses.add(sub.attr)
                    if isinstance(sub.ctx, ast.Store):
                        m.writes.add(sub.attr)
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                        and isinstance(sub.func.value, ast.Name) and receiver \
                        and sub.func.value.id == receiver:
                    m.calls.add(sub.func.attr)
            info.methods.append(m)
        elif isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name):
                    info.class_attrs.add(t.id)
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            if stmt.value is not None:
                info.class_attrs.add(stmt.target.id)
        elif isinstance(stmt, ast.ClassDef):
            classes.extend(collect_class(module, path, stmt, prefix=f"{qual}."))

    # atributos de estado: `self.x` só conta como estado de INSTÂNCIA em
    # métodos de instância; `cls.x` é estado de CLASSE (fachadas).
    for m in info.methods:
        if m.kind == "instance":
            info.instance_attrs |= m.writes
        elif m.kind == "class":
            info.class_attrs |= m.writes
    # ignora nomes de métodos que coincidem com atributos por acidente
    info.instance_attrs -= {m.name for m in info.methods if m.kind == "instance"}
    return classes


def collect_class_names(node: ast.ClassDef, out: set[str], out_dotted: set[str]):
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            out.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            d = dotted_name(sub)
            if d:
                out_dotted.add(d)
                out.add(d.split(".")[0])


def cohesion_metrics(info: ClassInfo) -> dict:
    methods = [m for m in info.methods if m.kind in ("instance", "class", "property")
               and not (m.name.startswith("__") and m.name.endswith("__"))]
    mcount = len(methods)
    attrs = info.instance_attrs
    a = len(attrs)

    pairs = [(i, j) for i in range(mcount) for j in range(i + 1, mcount)]
    shared = []
    for i, j in pairs:
        common = methods[i].accesses & methods[j].accesses & attrs
        if common:
            shared.append((i, j, common))
    q = len(shared)
    p = len(pairs) - q

    lcom1 = max(p - q, 0) if mcount >= 2 else None
    tcc = (q / len(pairs)) if pairs else None

    # variante com __init__ incluído (necessária para auditar o relatório
    # existente, que parece contá-lo)
    methods_init = [m for m in info.methods
                    if m.kind in ("instance", "class", "property")
                    and (m.name == "__init__" or not (m.name.startswith("__") and m.name.endswith("__")))]
    p2 = q2 = None
    lcom1_incl_init = None
    if len(methods_init) >= 2:
        pairs2 = [(i, j) for i in range(len(methods_init))
                  for j in range(i + 1, len(methods_init))]
        q2 = sum(1 for i, j in pairs2
                 if methods_init[i].accesses & methods_init[j].accesses & attrs)
        p2 = len(pairs2) - q2
        lcom1_incl_init = max(p2 - q2, 0)

    # LCOM* (Henderson-Sellers): a>0, m>1
    lcom_star = None
    if a > 0 and mcount > 1:
        total = sum(len(m.accesses & attrs) for m in methods)
        lcom_star = ((total / a) - mcount) / (1 - mcount)

    # LCOM4: componentes conexos (atributo compartilhado OU chamada direta)
    lcom4 = None
    if mcount > 0:
        parent = list(range(mcount))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        name_to_idx = {m.name: i for i, m in enumerate(methods)}
        for i in range(mcount):
            for j in range(i + 1, mcount):
                if methods[i].accesses & methods[j].accesses:
                    union(i, j)
        for i, m in enumerate(methods):
            for called in m.calls:
                if called in name_to_idx and name_to_idx[called] != i:
                    union(i, name_to_idx[called])
        lcom4 = len({find(i) for i in range(mcount)})

    # coesão de estado de CLASSE (para fachadas @classmethod)
    class_methods = [m for m in info.methods if m.kind == "class"
                     and not (m.name.startswith("__") and m.name.endswith("__"))]
    # constantes (UPPER_CASE) não são estado; config não conta como atributo coeso
    class_attrs = {a for a in info.class_attrs if not a.isupper()}
    lcom1_class = None
    if len(class_methods) >= 2 and class_attrs:
        cpairs = [(i, j) for i in range(len(class_methods)) for j in range(i + 1, len(class_methods))]
        cq = sum(1 for i, j in cpairs
                 if class_methods[i].accesses & class_methods[j].accesses & class_attrs)
        lcom1_class = max((len(cpairs) - cq) - cq, 0)

    if mcount < 2:
        applicability = "N/A: menos de 2 métodos de instância"
    elif a == 0:
        applicability = "N/A: sem atributos de instância"
    elif not any(m.accesses & attrs for m in methods if m.kind == "instance"):
        applicability = "N/A: nenhum método de instância usa o estado"
    else:
        applicability = "aplicavel"

    if a == 0 and class_attrs and class_methods:
        category = "estado de classe (fachada/@classmethod)"
    elif a == 0 and mcount == 0:
        category = "sem métodos de instância"
    elif a == 0:
        category = "funcional/sem estado de instância"
    elif not any(m.kind == "instance" for m in methods):
        category = "mista: estado de instância + métodos de classe"
    elif mcount <= 1:
        category = "estado unico"
    else:
        category = "estado de instancia"

    return {
        "instance_attrs": a,
        "class_attrs": len(class_attrs),
        "methods": mcount,
        "methods_all": len([m for m in info.methods]),
        "static_methods": len([m for m in info.methods if m.kind == "static"]),
        "class_methods": len([m for m in info.methods if m.kind == "class"]),
        "properties": len([m for m in info.methods if m.kind == "property"]),
        "shared_pairs": q,
        "nonshared_pairs": p,
        "total_pairs": len(pairs),
        "lcom1": lcom1,
        "lcom1_incl_init": lcom1_incl_init,
        "shared_pairs_incl_init": q2,
        "nonshared_pairs_incl_init": p2,
        "methods_incl_init": len(methods_init),
        "lcom_star": lcom_star,
        "lcom4": lcom4,
        "tcc": tcc,
        "lcom1_class_state": lcom1_class,
        "applicability": applicability,
        "category": category,
        "method_list": ";".join(m.name for m in methods),
    }


# --------------------------------------------------------------------------
# Radon
# --------------------------------------------------------------------------

def load_json(path: Path):
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def radon_summary(quality: Path) -> dict:
    cc = load_json(quality / "complexidade.json")
    hal = load_json(quality / "halstead.json")
    mi = load_json(quality / "manutenibilidade.json")
    raw = load_json(quality / "tamanho.json")
    return {"cc": cc, "hal": hal, "mi": mi, "raw": raw}


def cc_blocks(cc: dict) -> list[dict]:
    """Todos os blocos (função, método, classe) achatados.

    O JSON do CLI do Radon lista os métodos DUAS vezes (dentro da classe e
    como entrada de topo). Aqui os métodos de topo são descartados para não
    duplicar a contagem.
    """
    out = []
    for path, blocks in (cc or {}).items():
        for b in blocks:
            if b.get("type") == "method":
                continue
            row = {
                "module": module_from_path(path),
                "path": path,
                "type": b.get("type"),
                "name": b.get("name"),
                "classname": b.get("classname") or "",
                "lineno": b.get("lineno"),
                "endline": b.get("endline"),
                "complexity": b.get("complexity"),
                "rank": b.get("rank"),
            }
            row["length"] = (row["endline"] - row["lineno"] + 1) if row["endline"] else None
            out.append(row)
            for meth in b.get("methods") or []:
                out.append({
                    "module": row["module"],
                    "path": path,
                    "type": meth.get("type"),
                    "name": meth.get("name"),
                    "classname": meth.get("classname"),
                    "lineno": meth.get("lineno"),
                    "endline": meth.get("endline"),
                    "complexity": meth.get("complexity"),
                    "rank": meth.get("rank"),
                    "length": (meth["endline"] - meth["lineno"] + 1) if meth.get("endline") else None,
                })
    return out


def module_from_path(path: str) -> str:
    p = path.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    if p.endswith(".py"):
        p = p[:-3]
    if p.endswith("/__init__"):
        p = p[:-len("/__init__")]
    return p.replace("/", ".")


def mi_formula(volume: float, cc: int, sloc: int, comments: int) -> float:
    """Fórmula do Radon (radon/metrics.py::mi_compute)."""
    v = volume if volume > 0 else 1
    s = sloc if sloc > 0 else 1
    mi = (171 - 5.2 * math.log(v) - 0.23 * cc - 16.2 * math.log(s)
          + 50 * math.sin(math.sqrt(2.4 * comments)))
    return round(max(0.0, mi * 100 / 171), 5)


def mi_rank(mi: float) -> str:
    if mi > 19:
        return "A"
    if mi > 9:
        return "B"
    return "C"


# --------------------------------------------------------------------------
# Complexidade cognitiva (plugin externo)
# --------------------------------------------------------------------------

def qualname_at(tree: ast.Module, lineno: int) -> str:
    """Qualname da função/método mais interno que contém ``lineno``."""
    best = None

    def walk(node, prefix):
        nonlocal best
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = f"{prefix}{child.name}"
                end = getattr(child, "endline", getattr(child, "lineno", 0))
                if child.lineno <= lineno <= end:
                    if best is None or child.lineno >= best[0]:
                        best = (child.lineno, q)
                walk(child, q + ".")

    walk(tree, "")
    return best[1] if best else ""


def cognitive_complexity_report(root: Path, trees: dict[str, ast.Module], prod_nodes: set[str]):
    """Roda flake8-cognitive-complexity e devolve (linhas, status).

    Com --max-cognitive-complexity=0 o plugin reporta toda função com valor
    >= 1; funções ausentes têm valor 0. É uma implementação inspirada na
    especificação de Sonar (não o Sonar oficial).
    """
    targets = [t for t in ("nucleus", "orbits", "observatory", "server.py") if (root / t).exists()]
    cmd = [sys.executable, "-m", "flake8", "--select=CCR",
           "--max-cognitive-complexity=0",
           "--format=%(path)s|%(row)d|%(col)d|%(text)s", *targets]
    try:
        proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=900)
    except (OSError, subprocess.SubprocessError) as exc:
        return [], {"status": "pendente", "error": "falha_ao_executar_flake8",
                     "exception": type(exc).__name__,
                     "tool": "flake8-cognitive-complexity 0.1.0"}
    if "No module named flake8" in proc.stderr:
        return [], {"status": "pendente", "error": "flake8 não instalado", "tool": "flake8-cognitive-complexity 0.1.0"}

    rows = []
    for line in proc.stdout.splitlines():
        parts = line.split("|")
        if len(parts) != 4:
            continue
        raw_path, row, _col, text = parts
        m = re.search(r"\((\d+) > 0\)", text)
        if not m:
            continue
        path = Path(raw_path.replace("\\", "/"))
        try:
            mod = module_name(root, (root / path).resolve())
        except ValueError:
            continue
        if mod not in prod_nodes:
            continue
        tree = trees.get(mod)
        rows.append({
            "module": mod,
            "layer": layer_of(mod),
            "path": str(path).replace("\\", "/"),
            "lineno": int(row),
            "cognitive": int(m.group(1)),
            "qualname": qualname_at(tree, int(row)) if tree else "",
        })
    return rows, {
        "status": "ok",
        "tool": "flake8 7.4.1 + flake8-cognitive-complexity 0.1.0 (solar-like)",
        "files_scanned": len(targets),
        "functions_reported": len(rows),
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Métricas estruturais SOLAR")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--out-complexity", default=None)
    ap.add_argument("--quality", default=None)
    args = ap.parse_args()

    here = Path(__file__).resolve()
    root = Path(args.root).resolve() if args.root else here.parents[4]
    out = Path(args.out).resolve() if args.out else here.parents[1] / "dados"
    out_complexity = (
        Path(args.out_complexity).resolve()
        if args.out_complexity
        else here.parents[2] / "etapa_3_complexidade" / "dados"
    )
    quality = (
        Path(args.quality).resolve()
        if args.quality
        else here.parents[2] / "etapa_3_complexidade" / "dados" / "radon"
    )
    out.mkdir(parents=True, exist_ok=True)
    out_complexity.mkdir(parents=True, exist_ok=True)
    radon = radon_summary(quality)

    sources = iter_sources(root)
    internal = {m for m, _, is_test in sources if not is_test}
    trees: dict[str, ast.Module] = {}
    packages: dict[str, bool] = {}
    test_modules = {m for m, _, t in sources if t}

    parse_errors = []
    for mod, path, _ in sources:
        try:
            trees[mod] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            packages[mod] = is_package(path)
        except SyntaxError as exc:  # pragma: no cover
            parse_errors.append({"module": mod, "error": type(exc).__name__, "line": exc.lineno})

    # ---------------- grafo ----------------
    collectors: dict[str, ImportCollector] = {}
    edges: dict[str, set[str]] = defaultdict(set)
    edge_meta: dict[tuple[str, str], dict] = defaultdict(lambda: {"kinds": set(), "lines": []})
    external_edges: list[dict] = []
    unresolved = []

    for mod, tree in trees.items():
        col = ImportCollector(mod, packages.get(mod, False), internal)
        col.visit(tree)
        collectors[mod] = col
        for ref in col.refs:
            if ref.target:
                if ref.target == mod:
                    edges[mod].add(mod)  # auto-import (raro)
                    continue
                edges[mod].add(ref.target)
                key = (mod, ref.target)
                edge_meta[key]["kinds"].add(ref.kind)
                edge_meta[key]["lines"].append(ref.lineno)
            elif ref.external:
                external_edges.append({
                    "module": mod,
                    "external": ref.external,
                    "kind": ref.kind,
                    "lineno": ref.lineno,
                    "statement": ref.raw,
                    "is_test": mod in test_modules,
                })
            else:
                unresolved.append({"module": mod, "lineno": ref.lineno, "statement": ref.raw})

    # ---------------- imports dinâmicos ----------------
    # snapshot do grafo somente-estático, antes de acrescentar arestas dinâmicas
    static_edges_snapshot = {m: set(t) for m, t in edges.items()}

    # `importlib.import_module(...)` não é visível para o AST de imports.
    # Só entram alvos VERIFICÁVEIS:
    #   (a) literal de módulo interno: import_module("orbits.database.models")
    #   (b) varredura de pacote: import_module(f"{PKG}.{name}") após
    #       pkgutil.iter_modules -> dependência de PKG e de seus submódulos
    dynamic_edges = []

    def _dynamic_targets(mod: str, tree: ast.Module) -> None:
        consts: dict[str, str] = {}
        for stmt in ast.walk(tree):
            if isinstance(stmt, ast.Assign):
                targets = [t.id for t in stmt.targets if isinstance(t, ast.Name)]
                value = stmt.value
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                targets = [stmt.target.id]
                value = stmt.value
            else:
                continue
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                for t in targets:
                    consts[t] = value.value
        if not consts:
            return

        def _add(target: str, lineno: int, constant: str, kind: str):
            if target not in internal or target == mod:
                return
            dynamic_edges.append({"source": mod, "target": target, "lineno": lineno,
                                  "constant": constant, "kind": kind})
            edges[mod].add(target)
            key = (mod, target)
            edge_meta[key]["kinds"].add("dynamic")
            edge_meta[key]["lines"].append(lineno)

        for call in ast.walk(tree):
            if not isinstance(call, ast.Call):
                continue
            fn = call.func
            is_dyn = ((isinstance(fn, ast.Attribute) and fn.attr == "import_module")
                      or (isinstance(fn, ast.Name) and fn.id == "__import__"))
            if not is_dyn or not call.args:
                continue
            arg = call.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                _add(arg.value, call.lineno, arg.value, "literal")
            elif isinstance(arg, ast.JoinedStr):
                values = [p for p in arg.values if isinstance(p, ast.FormattedValue)]
                if len(values) < 2:
                    continue
                expr = values[0].value
                name = expr.attr if isinstance(expr, ast.Attribute) else getattr(expr, "id", None)
                if name in consts:
                    pkg = consts[name]
                    _add(pkg, call.lineno, name, "package_scan")
                    for other in internal:
                        if other.startswith(pkg + "."):
                            _add(other, call.lineno, name, "package_scan")

    for mod, tree in trees.items():
        _dynamic_targets(mod, tree)

    prod_nodes = set(internal)
    prod_edges = {m: {t for t in tgts if t in prod_nodes}
                  for m, tgts in edges.items() if m in prod_nodes}
    prod_edges = {m: t for m, t in prod_edges.items() if t}

    ca = Counter()
    ce = Counter()
    for src, tgts in prod_edges.items():
        ce[src] = len(tgts)
        for t in tgts:
            ca[t] += 1

    test_fan_in = Counter()
    for src, tgts in edges.items():
        if src in test_modules:
            for t in tgts:
                if t in prod_nodes:
                    test_fan_in[t] += 1

    # ---------------- ciclos ----------------
    sccs = strongly_connected_components(sorted(prod_nodes), prod_edges)
    cycles = []
    self_loops = []
    for comp in sccs:
        if len(comp) > 1:
            cs = set(comp)
            inner = sorted((s, t) for s in comp for t in prod_edges.get(s, ()) if t in cs)
            cycles.append({"size": len(comp), "modules": sorted(comp), "edges": len(inner),
                           "edges_list": [f"{s} -> {t}" for s, t in inner]})
        elif comp and comp[0] in prod_edges.get(comp[0], set()):
            self_loops.append(comp[0])
    cycles.sort(key=lambda c: (-c["size"], c["modules"][0]))

    # mesmo cálculo no grafo SOMENTE ESTÁTICO (para separar o efeito dos imports dinâmicos)
    static_prod_edges = {m: {t for t in tgts if t in prod_nodes}
                         for m, tgts in static_edges_snapshot.items() if m in prod_nodes}
    static_sccs = strongly_connected_components(sorted(prod_nodes), static_prod_edges)
    static_cycles = []
    for comp in static_sccs:
        if len(comp) > 1:
            cs = set(comp)
            inner = sorted((s, t) for s in comp for t in static_prod_edges.get(s, ()) if t in cs)
            static_cycles.append({"size": len(comp), "modules": sorted(comp), "edges": len(inner),
                                  "edges_list": [f"{s} -> {t}" for s, t in inner]})
        elif comp and comp[0] in static_prod_edges.get(comp[0], set()):
            static_cycles.append({"size": 1, "modules": comp, "edges": 1,
                                  "edges_list": [f"{comp[0]} -> {comp[0]}"]})
    static_cycles.sort(key=lambda c: (-c["size"], c["modules"][0]))

    # ---------------- alcancabilidade a partir dos pontos de entrada ----------------
    # Pontos de entrada declarados explicitamente (não inferidos).
    ENTRY_POINTS = ["server", "observatory.solar.__main__"]
    reachable = {m for m in ENTRY_POINTS if m in prod_nodes}
    queue = list(reachable)
    while queue:
        node = queue.pop()
        for nxt in prod_edges.get(node, ()):
            if nxt not in reachable:
                reachable.add(nxt)
                queue.append(nxt)

    # ---------------- classes ----------------
    class_infos: list[ClassInfo] = []
    for mod, tree in trees.items():
        if mod in test_modules:
            continue
        path = str(next(p for m, p, _ in sources if m == mod).relative_to(root)).replace("\\", "/")
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_infos.extend(collect_class(mod, path, node))

    class_qnames = {c.qualname for c in class_infos}
    class_by_simple = defaultdict(set)
    for c in class_infos:
        class_by_simple[c.name].add(c.qualname)
        class_by_simple[c.qualname.split(".")[-1]].add(c.qualname)

    def resolve_class(name: str, mod: str) -> tuple[set[str], set[str]]:
        """(resolvidos, ambíguos) para um nome simples ou cadeia pontuada."""
        imports = collectors[mod].symbols if mod in collectors else {}
        parts = name.split(".")
        root_name = parts[0]
        if root_name in imports:
            kind, qual = imports[root_name]
            if kind == "module":
                target = qual + ("." + ".".join(parts[1:]) if len(parts) > 1 else "")
                if target in class_qnames:
                    return {target}, set()
                return set(), set()
            if kind == "symbol":
                if qual in class_qnames:
                    return {qual}, set()
                return set(), set()
        if len(parts) > 1:
            return set(), set()
        cands = class_by_simple.get(name, set())
        if len(cands) == 1:
            return set(cands), set()
        if len(cands) > 1:
            return set(), set(cands)
        return set(), set()

    def resolve_external(name: str, mod: str) -> str | None:
        imports = collectors[mod].symbols if mod in collectors else {}
        root_name = name.split(".")[0]
        if root_name in imports:
            kind, qual = imports[root_name]
            if kind in ("external_symbol", "external_module") and qual.split(".")[-1][:1].isupper():
                return qual
        return None

    # 1ª passada: nomes usados em cada classe
    infos_by_qual = {c.qualname: c for c in class_infos}
    for mod, tree in trees.items():
        if mod in test_modules:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                qual = next((c.qualname for c in class_infos
                             if c.module == mod and c.lineno == node.lineno), None)
                if not qual:
                    continue
                info = infos_by_qual[qual]
                collect_class_names(node, info.names, info.dotted)

    # 2ª passada: resolver nomes -> classes internas / externas
    for info in class_infos:
        for name in info.names:
            if name == info.name:
                continue
            got, amb = resolve_class(name, info.module)
            info.cbo_internal_min |= got
            info.cbo_internal_max |= got | amb
            info.cbo_ambiguous |= amb
            ext = resolve_external(name, info.module)
            if ext:
                info.cbo_external.add(ext)
        for d in info.dotted:
            got, amb = resolve_class(d, info.module)
            info.cbo_internal_min |= got
            info.cbo_internal_max |= got | amb
            info.cbo_ambiguous |= amb
            ext = resolve_external(d.split(".")[-1], info.module)
            if ext:
                info.cbo_external.add(ext)

    for info in class_infos:
        info.cbo_internal_min = {q for q in info.cbo_internal_min if q != info.qualname}
        info.cbo_internal_max = {q for q in info.cbo_internal_max if q != info.qualname}
        # remover herança de si mesmo
        info.cbo_internal_min -= {info.qualname}
        info.cbo_internal_max -= {info.qualname}

    # ---------------- escrita: acoplamento ----------------
    mod_rows = []
    for mod in sorted(prod_nodes):
        path = next(p for m, p, _ in sources if m == mod)
        r = (radon["raw"] or {}).get(str(path.relative_to(root)).replace("\\", "/"), {})
        total = ca[mod] + ce[mod]
        mod_rows.append({
            "module": mod,
            "layer": layer_of(mod),
            "sublayer": sublayer_of(mod),
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "Ca": ca[mod],
            "Ce": ce[mod],
            "instability": round(ce[mod] / total, 4) if total else "",
            "fan_in_tests": test_fan_in[mod],
            "sloc": r.get("sloc", ""),
            "lloc": r.get("lloc", ""),
        })
    with (out / "modulos_acoplamento.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(mod_rows[0].keys()))
        w.writeheader()
        w.writerows(mod_rows)

    dep_rows = []
    for (s, t), meta in sorted(edge_meta.items()):
        if s in test_modules:
            continue
        dep_rows.append({
            "source": s,
            "target": t,
            "source_layer": layer_of(s),
            "target_layer": layer_of(t),
            "kinds": "|".join(sorted(meta["kinds"])),
            "lines": "|".join(str(x) for x in sorted(meta["lines"])),
        })
    with (out / "dependencias_internas.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(dep_rows[0].keys()))
        w.writeheader()
        w.writerows(dep_rows)

    with (out / "dependencias_externas.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["module", "external", "kind", "lineno", "statement", "is_test"])
        w.writeheader()
        w.writerows(sorted(external_edges, key=lambda r: (r["module"], r["lineno"])))

    with (out / "ciclos_scc.json").open("w", encoding="utf-8") as fh:
        json.dump({
            "nodes": len(prod_nodes),
            "edges": sum(len(v) for v in prod_edges.values()),
            "scc_count": len(sccs),
            "static": {
                "edges": sum(len(v) for v in static_prod_edges.values()),
                "cycles": static_cycles,
            },
            "dynamic_edges": dynamic_edges,
            "cycles": cycles,
            "self_loops": self_loops,
        }, fh, indent=2, ensure_ascii=False)

    with (out / "solar_ciclos_internos.json").open("w", encoding="utf-8") as fh:
        json.dump({
            "metodologia": {
                "nos": "módulos internos de produção (tests/ excluídos)",
                "arestas": "import AST + imports dinâmicos verificáveis (importlib.import_module)",
                "algoritmo": "Tarjan iterativo (componentes fortemente conexos)",
                "auto_imports": "incluídos em self_loops",
            },
            "estatisticas": {
                "modulos": len(prod_nodes),
                "arestas_estaticas": sum(len(v) for v in static_prod_edges.values()),
                "arestas_dinamicas": len(dynamic_edges),
                "arestas_totais": sum(len(v) for v in prod_edges.values()),
                "ciclos_estaticos": len(static_cycles),
                "ciclos_totais": len(cycles),
            },
            "ciclos_estaticos": static_cycles,
            "imports_dinamicos": dynamic_edges,
            "ciclos": cycles,
            "auto_imports": self_loops,
        }, fh, indent=2, ensure_ascii=False)

    # ---------------- escrita: CBO + coesão ----------------
    cbo_rows = []
    coh_rows = []
    for info in sorted(class_infos, key=lambda c: c.qualname):
        coh = cohesion_metrics(info)
        cbo_rows.append({
            "class": info.qualname,
            "module": info.module,
            "layer": layer_of(info.module),
            "path": info.path,
            "lineno": info.lineno,
            "cbo_internal_min": len(info.cbo_internal_min),
            "cbo_internal_max": len(info.cbo_internal_max),
            "cbo_external_est": len(info.cbo_external),
            "ambiguous_names": ";".join(sorted(info.cbo_ambiguous)),
            "targets_internal": ";".join(sorted(info.cbo_internal_max)),
            "targets_external": ";".join(sorted(info.cbo_external)),
        })
        row = {
            "class": info.qualname,
            "module": info.module,
            "layer": layer_of(info.module),
            "path": info.path,
            "lineno": info.lineno,
            "category": coh["category"],
            "applicability": coh["applicability"],
            **{k: v for k, v in coh.items() if k not in ("category", "applicability")},
        }
        coh_rows.append(row)

    with (out / "classes_cbo.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cbo_rows[0].keys()))
        w.writeheader()
        w.writerows(cbo_rows)

    with (out / "coesao_classes.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(coh_rows[0].keys()))
        w.writeheader()
        w.writerows(coh_rows)

    # ---------------- arquivos com os nomes canônicos do estudo ----------------
    cbo_by_module = defaultdict(list)
    for r in cbo_rows:
        cbo_by_module[r["module"]].append(r["cbo_internal_max"])

    solar_acoplamento = []
    for r in mod_rows:
        solar_acoplamento.append({
            "module": r["module"],
            "layer": r["layer"],
            "sublayer": r["sublayer"],
            "Ca_interno": r["Ca"],
            "Ce_interno": r["Ce"],
            "instabilidade": r["instability"],
            "fan_in_testes": r["fan_in_tests"],
            "cbo_classes_max": max(cbo_by_module.get(r["module"], [0])) if cbo_by_module.get(r["module"]) else 0,
            "sloc": r["sloc"],
            "lloc": r["lloc"],
        })
    with (out / "solar_acoplamento_modulos.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(solar_acoplamento[0].keys()))
        w.writeheader()
        w.writerows(solar_acoplamento)

    with (out / "solar_cbo_classes_estimado.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        fields = ["class", "module", "layer", "path", "lineno", "cbo_internal_min",
                  "cbo_internal_max", "cbo_external_est", "ambiguous_names",
                  "targets_internal", "targets_external"]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows([{k: r[k] for k in fields} for r in
                     sorted(cbo_rows, key=lambda r: (-r["cbo_internal_max"], r["class"]))])

    with (out / "solar_cbo_coesao_validacao.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(coh_rows[0].keys()))
        w.writeheader()
        w.writerows(sorted(coh_rows, key=lambda r: (
            r["applicability"] != "aplicavel",
            -(r["lcom1"] if isinstance(r["lcom1"], int) else -1),
            r["class"],
        )))

    # ---------------- camadas ----------------
    layer_rows = []
    layers = sorted({layer_of(m) for m in prod_nodes})
    for lay in layers:
        mods = [m for m in prod_nodes if layer_of(m) == lay]
        ce_l = sum(ce[m] for m in mods)
        ca_l = sum(ca[m] for m in mods)
        cross_out = {(s, t) for s, tgts in prod_edges.items() if layer_of(s) == lay
                     for t in tgts if layer_of(t) != lay}
        cross_in = {(s, t) for s, tgts in prod_edges.items() if layer_of(s) != lay
                    for t in tgts if layer_of(t) == lay}
        layer_rows.append({
            "layer": lay,
            "modules": len(mods),
            "internal_edges_out": sum(len(prod_edges.get(m, ())) for m in mods),
            "Ce_sum": ce_l,
            "Ca_sum": ca_l,
            "instability_sum_based": round(ce_l / (ca_l + ce_l), 4) if (ca_l + ce_l) else "",
            "cross_layer_out_edges": len(cross_out),
            "cross_layer_in_edges": len(cross_in),
            "classes": sum(1 for c in class_infos if layer_of(c.module) == lay),
        })
    with (out / "camadas_resumo.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(layer_rows[0].keys()))
        w.writeheader()
        w.writerows(layer_rows)

    # ---------------- radon: funções e módulos ----------------
    blocks = cc_blocks(radon["cc"] or {})
    funcs = [b for b in blocks if b["type"] in ("function", "method")]
    for b in funcs:
        b["layer"] = layer_of(b["module"])
    with (out_complexity / "funcoes_complexidade.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(funcs[0].keys()))
        w.writeheader()
        w.writerows(sorted(funcs, key=lambda b: (-(b["complexity"] or 0), b["module"], b["lineno"] or 0)))

    raw_map = {module_from_path(k): v for k, v in (radon["raw"] or {}).items()}
    hal_map = {module_from_path(k): v for k, v in (radon["hal"] or {}).items()}
    mi_map = {module_from_path(k): v for k, v in (radon["mi"] or {}).items()}

    per_mod_cc = defaultdict(list)
    for b in funcs:
        per_mod_cc[b["module"]].append(b["complexity"] or 0)

    # ---------------- complexidade cognitiva (flake8-cognitive-complexity) ----------------
    cognitive_rows, cognitive_status = cognitive_complexity_report(root, trees, prod_nodes)

    hal_rows = []
    hal_zero = 0
    hal_funcs_total = 0
    for mod in sorted(hal_map):
        h = hal_map[mod]
        total = h.get("total", {})
        funcs_h = h.get("functions", {})
        zeros = sum(1 for v in funcs_h.values() if (v.get("N1", 0) + v.get("N2", 0)) == 0)
        hal_zero += zeros
        hal_funcs_total += len(funcs_h)
        hal_rows.append({
            "module": mod,
            "layer": layer_of(mod),
            "h1": total.get("h1"),
            "h2": total.get("h2"),
            "N1": total.get("N1"),
            "N2": total.get("N2"),
            "volume": round(total.get("volume", 0.0), 4),
            "difficulty": round(total.get("difficulty", 0.0), 4),
            "effort": round(total.get("effort", 0.0), 4),
            "bugs": round(total.get("bugs", 0.0), 6),
            "functions": len(funcs_h),
            "functions_zero_halstead": zeros,
        })
    with (out_complexity / "radon_halstead_modulos.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(hal_rows[0].keys()))
        w.writeheader()
        w.writerows(hal_rows)

    # ---------------- complexidade cognitiva: escrita ----------------
    cognitive_by_module = defaultdict(list)
    for r in cognitive_rows:
        cognitive_by_module[r["module"]].append(r["cognitive"])
    if cognitive_rows:
        with (out_complexity / "complexidade_cognitiva.csv").open("w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(cognitive_rows[0].keys()))
            w.writeheader()
            w.writerows(sorted(cognitive_rows, key=lambda r: (-r["cognitive"], r["module"], r["lineno"])))

    # ---------------- consolidado por módulo ----------------
    merged = []
    for mod in sorted(prod_nodes):
        path = next(p for m, p, _ in sources if m == mod)
        key = str(path.relative_to(root)).replace("\\", "/")
        ccs = per_mod_cc.get(mod, [])
        h = hal_map.get(mod, {}).get("total", {})
        r = raw_map.get(mod, {})
        mi = mi_map.get(mod, {})
        cog = cognitive_by_module.get(mod, [])
        mi_alt = ""
        try:
            from radon.metrics import mi_visit  # type: ignore
            mi_alt = round(mi_visit(path.read_text(encoding="utf-8"), False), 5)
        except ImportError:  # pragma: no cover
            mi_alt = ""
        merged.append({
            "module": mod,
            "layer": layer_of(mod),
            "sublayer": sublayer_of(mod),
            "path": key,
            "sloc": r.get("sloc", ""),
            "lloc": r.get("lloc", ""),
            "comments": r.get("comments", ""),
            "functions_methods": len(ccs),
            "cc_sum": sum(ccs),
            "cc_mean": round(statistics.fmean(ccs), 3) if ccs else "",
            "cc_max": max(ccs) if ccs else "",
            "halstead_volume": round(h.get("volume", 0.0), 4),
            "halstead_difficulty": round(h.get("difficulty", 0.0), 4),
            "mi": mi.get("mi", ""),
            "mi_rank": mi.get("rank", ""),
            "mi_sem_multiline": mi_alt,
            "cognitive_functions_ge1": len(cog),
            "cognitive_sum": sum(cog),
            "cognitive_max": max(cog) if cog else 0,
            "Ca": ca[mod],
            "Ce": ce[mod],
            "instability": round(ce[mod] / (ca[mod] + ce[mod]), 4) if (ca[mod] + ce[mod]) else "",
            "fan_in_tests": test_fan_in[mod],
            "alcancavel": "sim" if mod in reachable else "nao",
        })
    with (out / "modulos_metricas.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(merged[0].keys()))
        w.writeheader()
        w.writerows(merged)

    # ---------------- consolidado por camada ----------------
    layer_agg = []
    for lay in layers:
        ms = [m for m in merged if m["layer"] == lay]
        ccs = [m["cc_sum"] for m in ms if m["functions_methods"]]
        mis = [m["mi"] for m in ms if m["mi"] != ""]
        cbo_vals = [c["cbo_internal_max"] for c in cbo_rows if c["layer"] == lay]
        lcom_vals = [r["lcom1"] for r in coh_rows
                     if r["layer"] == lay and r["applicability"] == "aplicavel" and r["lcom1"] is not None]
        layer_agg.append({
            "layer": lay,
            "modules": len(ms),
            "classes": len([c for c in class_infos if layer_of(c.module) == lay]),
            "sloc": sum(m["sloc"] for m in ms),
            "lloc": sum(m["lloc"] for m in ms),
            "functions_methods": sum(m["functions_methods"] for m in ms),
            "cc_sum": sum(m["cc_sum"] for m in ms),
            "cc_mean_per_function": round(sum(m["cc_sum"] for m in ms) / sum(m["functions_methods"] for m in ms), 3)
            if sum(m["functions_methods"] for m in ms) else "",
            "cc_max": max((m["cc_max"] for m in ms if m["cc_max"] != ""), default=""),
            "cognitive_functions_ge1": sum(m["cognitive_functions_ge1"] for m in ms),
            "cognitive_sum": sum(m["cognitive_sum"] for m in ms),
            "cognitive_max": max((m["cognitive_max"] for m in ms), default=0),
            "halstead_volume": round(sum(m["halstead_volume"] for m in ms), 3),
            "mi_mean": round(statistics.fmean(mis), 3) if mis else "",
            "mi_min": min(mis) if mis else "",
            "Ca_sum": sum(m["Ca"] for m in ms),
            "Ce_sum": sum(m["Ce"] for m in ms),
            "instability_sum_based": round(sum(m["Ce"] for m in ms) / (sum(m["Ca"] for m in ms) + sum(m["Ce"] for m in ms)), 4)
            if (sum(m["Ca"] for m in ms) + sum(m["Ce"] for m in ms)) else "",
            "cbo_mean": round(statistics.fmean(cbo_vals), 3) if cbo_vals else "",
            "cbo_max": max(cbo_vals) if cbo_vals else 0,
            "lcom1_applicable": len(lcom_vals),
            "lcom1_mean": round(statistics.fmean(lcom_vals), 3) if lcom_vals else "",
        })
    with (out / "camadas_consolidado.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(layer_agg[0].keys()))
        w.writeheader()
        w.writerows(layer_agg)

    # ---------------- consolidado por subcamada ----------------
    sub_agg = []
    for sub in sorted({m["sublayer"] for m in merged}):
        ms = [m for m in merged if m["sublayer"] == sub]
        ccs = [m["cc_sum"] for m in ms]
        mis = [m["mi"] for m in ms if m["mi"] != ""]
        sub_agg.append({
            "sublayer": sub,
            "layer": ms[0]["layer"],
            "modules": len(ms),
            "sloc": sum(m["sloc"] for m in ms),
            "functions_methods": sum(m["functions_methods"] for m in ms),
            "cc_sum": sum(ccs),
            "cc_max": max((m["cc_max"] for m in ms if m["cc_max"] != ""), default=""),
            "mi_mean": round(statistics.fmean(mis), 2) if mis else "",
            "Ca_sum": sum(m["Ca"] for m in ms),
            "Ce_sum": sum(m["Ce"] for m in ms),
            "cbo_max": max([max(cbo_by_module.get(m["module"], [0])) for m in ms], default=0),
            "cognitive_sum": sum(m["cognitive_sum"] for m in ms),
        })
    with (out / "subcamadas_resumo.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sub_agg[0].keys()))
        w.writeheader()
        w.writerows(sub_agg)

    # ---------------- alcancabilidade: escrita ----------------
    unreachable = []
    for m in sorted(prod_nodes - reachable):
        path = next(p for mm, p, _ in sources if mm == m)
        tree = trees.get(m)
        has_code = bool(tree) and any(
            not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))
            for n in tree.body
        )
        if not has_code:
            continue
        unreachable.append({
            "module": m,
            "layer": layer_of(m),
            "sloc": raw_map.get(m, {}).get("sloc", 0),
            "ce": ce[m],
            "ca": ca[m],
        })
    reach = {
        "entry_points": ENTRY_POINTS,
        "metodo": "BFS nas arestas internas de produção a partir dos pontos de entrada declarados",
        "modulos_alcancaveis": len(reachable),
        "modulos_producao": len(prod_nodes),
        "nao_alcancaveis_com_codigo": unreachable,
        "sloc_nao_alcancavel": sum(u["sloc"] for u in unreachable),
        "sloc_producao": sum(m["sloc"] for m in merged),
        "observacao": ("Módulo alcançável apenas por testes não é contado como alcançável; "
                       "inicializadores de pacote vazios são omitidos desta lista."),
    }
    with (out / "alcancabilidade.json").open("w", encoding="utf-8") as fh:
        json.dump(reach, fh, indent=2, ensure_ascii=False)

    # ---------------- matriz camada -> camada ----------------
    matrix = Counter()
    for s, tgts in prod_edges.items():
        for t in tgts:
            matrix[(layer_of(s), layer_of(t))] += 1
    with (out / "matriz_camadas.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["from_layer", "to_layer", "edges"])
        for (a, b), n in sorted(matrix.items()):
            w.writerow([a, b, n])

    # ---------------- validação do MI ----------------
    mi_validation = {
        "status": "ok",
        "tool": "radon 6.0.1 — radon.metrics.mi_visit(fonte, multi=True)",
        "modules": 0,
        "mismatch_count": 0,
        "max_abs_diff": None,
        "mismatches": [],
        "formula": (
            "MI = max(0, min(100, (171 - 5.2*ln(V) - 0.23*CC − 16.2*ln(LLOC) "
            "+ 50*sin(sqrt(2.46*radians(%comentários)))) * 100/171)); "
            "100 quando V<=0 ou LLOC<=0"
        ),
        "notes": [
            "V = volume de Halstead total do arquivo (radon h_visit_ast)",
            "CC = ComplexityVisitor.total_complexity (não é a soma dos blocos do relatório cc)",
            "LLOC = radon raw.lloc (não SLOC)",
            "%comentários = (comments + multi) / sloc * 100",
        ],
    }
    try:
        from radon.metrics import mi_visit  # type: ignore

        diffs = []
        for key, rec in (radon["mi"] or {}).items():
            src = (root / key).read_text(encoding="utf-8")
            calc = mi_visit(src, True)
            diff = abs(calc - rec.get("mi", 0.0))
            diffs.append(diff)
            if diff > 1e-6:
                mi_validation["mismatches"].append({
                    "file": key, "reported": rec.get("mi"), "recomputed": calc})
        mi_validation.update({
            "modules": len(diffs),
            "mismatch_count": len(mi_validation["mismatches"]),
            "max_abs_diff": round(max(diffs), 9) if diffs else None,
            "mean_abs_diff": round(statistics.fmean(diffs), 12) if diffs else None,
        })
    except ImportError:  # pragma: no cover
        mi_validation["status"] = "pendente: radon não instalado"
    mi_report = mi_validation

    # ---------------- reprodução integral do Radon (cc / hal / raw) ----------------
    reproduction = {"status": "ok", "cc_mismatches": 0, "hal_mismatches": 0,
                    "raw_mismatches": 0, "files_checked": 0, "examples": []}
    try:
        from radon.complexity import cc_visit  # type: ignore
        from radon.metrics import analyze, h_visit  # type: ignore

        for key, cc_json_blocks in (radon["cc"] or {}).items():
            src = (root / key).read_text(encoding="utf-8")
            expected = {(b.get("type"), b.get("name"), b.get("lineno"), b.get("complexity"))
                        for b in cc_json_blocks if b.get("type") in ("class", "function")}
            got = {(b.__class__.__name__.lower(), b.name, b.lineno, b.complexity)
                   for b in cc_visit(src)
                   if not getattr(b, "classname", None)}
            if expected != got:
                reproduction["cc_mismatches"] += 1
                if len(reproduction["examples"]) < 5:
                    reproduction["examples"].append({"file": key, "metric": "cc"})
        for key, rec in (radon["hal"] or {}).items():
            src = (root / key).read_text(encoding="utf-8")
            vol = h_visit(src).total.volume
            if abs(vol - rec.get("total", {}).get("volume", 0.0)) > 1e-6:
                reproduction["hal_mismatches"] += 1
                if len(reproduction["examples"]) < 5:
                    reproduction["examples"].append({"file": key, "metric": "hal"})
        for key, rec in (radon["raw"] or {}).items():
            src = (root / key).read_text(encoding="utf-8")
            a = analyze(src)
            if (a.lloc, a.sloc, a.comments) != (rec.get("lloc"), rec.get("sloc"), rec.get("comments")):
                reproduction["raw_mismatches"] += 1
                if len(reproduction["examples"]) < 5:
                    reproduction["examples"].append({"file": key, "metric": "raw"})
        reproduction["files_checked"] = len(radon["cc"] or {})
        reproduction["total_mismatches"] = (reproduction["cc_mismatches"]
                                            + reproduction["hal_mismatches"]
                                            + reproduction["raw_mismatches"])
    except ImportError:  # pragma: no cover
        reproduction["status"] = "pendente: radon não instalado"
    mi_report["full_reproduction"] = reproduction

    # ---------------- resumo ----------------
    def dist(values):
        vals = sorted(v for v in values if v is not None)
        if not vals:
            return {}
        return {
            "n": len(vals),
            "min": vals[0],
            "median": statistics.median(vals),
            "mean": round(statistics.fmean(vals), 3),
            "p90": vals[min(len(vals) - 1, int(len(vals) * 0.9))],
            "max": vals[-1],
            "sum": sum(vals),
        }

    ranks = Counter(b["rank"] for b in funcs)
    prod_funcs = [b for b in funcs if layer_of(b["module"]) != "Tests"]
    summary = {
        "root": str(root),
        "files_parsed": len(trees),
        "parse_errors": parse_errors,
        "production_modules": len(prod_nodes),
        "test_modules": len(test_modules),
        "internal_edges": sum(len(v) for v in prod_edges.values()),
        "external_import_statements": len(external_edges),
        "unresolved_imports": len(unresolved),
        "dynamic_imports": dynamic_edges,
        "cycles": {
            "count": len(cycles),
            "modules_in_cycles": sum(c["size"] for c in cycles),
            "largest": cycles[0]["size"] if cycles else 0,
            "static_count": len(static_cycles),
            "dynamic_only": len(cycles) - len(static_cycles),
        },
        "reachability": {
            "entry_points": ENTRY_POINTS,
            "reachable_modules": len(reachable),
            "unreachable_with_code": len(unreachable),
            "unreachable_sloc": sum(u["sloc"] for u in unreachable),
            "production_sloc": sum(m["sloc"] for m in merged),
            "modules": [u["module"] for u in unreachable],
        },
        "self_loops": self_loops,
        "coupling": {
            "Ce": dist(list(ce.values())),
            "Ca": dist(list(ca.values())),
            "top_Ce": [{"module": m, "Ce": ce[m]}
                       for m in sorted(ce, key=lambda x: (-ce[x], x))[:10]],
            "top_Ca": [{"module": m, "Ca": ca[m]}
                       for m in sorted(ca, key=lambda x: (-ca[x], x))[:10]],
            "top_instability": [
                {"module": m, "Ca": ca[m], "Ce": ce[m],
                 "I": round(ce[m] / (ca[m] + ce[m]), 3)}
                for m in sorted(
                    (x for x in prod_nodes if ce[x] + ca[x] >= 3),
                    key=lambda x: (-(ce[x] / (ca[x] + ce[x])), x))
            ][:10],
        },
        "classes": {
            "total": len(class_infos),
            "with_instance_state": sum(1 for r in coh_rows if r["instance_attrs"] > 0),
            "without_instance_state": sum(1 for r in coh_rows if r["instance_attrs"] == 0),
            "applicable_lcom": sum(1 for r in coh_rows if r["applicability"] == "aplicavel"),
            "not_applicable_lcom": sum(1 for r in coh_rows if r["applicability"] != "aplicavel"),
            "lcom1": dist([r["lcom1"] for r in coh_rows if r["applicability"] == "aplicavel"]),
            "lcom1_na": dist([r["lcom1"] for r in coh_rows if r["applicability"] != "aplicavel"]),
            "lcom4": dist([r["lcom4"] for r in coh_rows if r["applicability"] == "aplicavel"]),
            "tcc": dist([r["tcc"] for r in coh_rows if r["applicability"] == "aplicavel"]),
            "lcom1_worst": sorted(
                [{"class": r["class"], "lcom1": r["lcom1"], "lcom4": r["lcom4"],
                  "tcc": r["tcc"], "attrs": r["instance_attrs"], "methods": r["methods"]}
                 for r in coh_rows if r["applicability"] == "aplicavel" and r["lcom1"] is not None],
                key=lambda x: -x["lcom1"])[:10],
            "cbo_internal": dist([r["cbo_internal_max"] for r in cbo_rows]),
            "cbo_worst": sorted(
                [{"class": r["class"], "cbo_min": r["cbo_internal_min"],
                  "cbo_max": r["cbo_internal_max"]} for r in cbo_rows],
                key=lambda x: -x["cbo_max"])[:10],
        },
        "complexity": {
            "blocks_all": len(blocks),
            "functions_methods": len(funcs),
            "functions_methods_production": len(prod_funcs),
            "cc_total_production": dist([b["complexity"] for b in prod_funcs]),
            "rank_distribution_production": dict(Counter(b["rank"] for b in prod_funcs)),
            "worst_functions": [
                {"module": b["module"], "name": b["name"], "class": b["classname"],
                 "cc": b["complexity"], "rank": b["rank"], "length": b["length"],
                 "lineno": b["lineno"]}
                for b in sorted(prod_funcs, key=lambda b: (-(b["complexity"] or 0)))[:15]
            ],
            "length": dist([b["length"] for b in prod_funcs]),
            "longest": [
                {"module": b["module"], "name": b["name"], "cc": b["complexity"], "length": b["length"]}
                for b in sorted(prod_funcs, key=lambda b: -(b["length"] or 0))[:10]
            ],
        },
        "halstead": {
            "modules": len(hal_rows),
            "functions_total": hal_funcs_total,
            "functions_with_zero_n1_n2": hal_zero,
            "zero_ratio": round(hal_zero / hal_funcs_total, 4) if hal_funcs_total else None,
            "volume_total": round(sum(r["volume"] for r in hal_rows), 3),
            "volume_production": round(sum(r["volume"] for r in hal_rows if r["layer"] != "Tests"), 3),
        },
        "cognitive": {
            **cognitive_status,
            "modules_with_score_gt0": len(cognitive_by_module),
            "total_score": sum(r["cognitive"] for r in cognitive_rows),
            "distribution": dist([r["cognitive"] for r in cognitive_rows]),
            "worst": [
                {"module": r["module"], "qualname": r["qualname"], "cognitive": r["cognitive"],
                 "lineno": r["lineno"]}
                for r in sorted(cognitive_rows, key=lambda r: (-r["cognitive"], r["module"]))[:15]
            ],
        },
        "maintainability": {
            "reported_modules": len(mi_map),
            "mi": dist([v.get("mi") for v in mi_map.values()]),
            "rank_distribution": dict(Counter(v.get("rank") for v in mi_map.values())),
            "rank_distribution_production": dict(Counter(
                v.get("rank") for k, v in mi_map.items() if layer_of(k) != "Tests")),
            "mi_production": dist([m["mi"] for m in merged if m["mi"] != ""]),
            "mi_production_sem_multiline": dist(
                [m["mi_sem_multiline"] for m in merged if m["mi_sem_multiline"] != ""]),
            "sensibilidade_multiline": {
                "descricao": "MI recalculado com count_multi=False (docstrings não contam como comentário)",
                "n": len(merged),
                "delta_medio": round(statistics.fmean(
                    [m["mi_sem_multiline"] - m["mi"] for m in merged
                     if m["mi"] != "" and m["mi_sem_multiline"] != ""]), 3),
                "modulos_com_delta_abs_maior_10": sum(
                    1 for m in merged if m["mi"] != "" and m["mi_sem_multiline"] != ""
                    and abs(m["mi_sem_multiline"] - m["mi"]) > 10),
            },
            "recomputation": mi_report,
        },
        "layers": layer_rows,
        "radon_reports": {
            "cc_files": len(radon["cc"] or {}),
            "hal_files": len(radon["hal"] or {}),
            "mi_files": len(radon["mi"] or {}),
            "raw_files": len(radon["raw"] or {}),
        },
    }
    with (out / "resumo_metricas.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    with (out_complexity / "validacao_radon.json").open("w", encoding="utf-8") as fh:
        json.dump(mi_report, fh, indent=2, ensure_ascii=False)

    print(json.dumps({
        "modulos_producao": summary["production_modules"],
        "modulos_teste": summary["test_modules"],
        "arestas_internas": summary["internal_edges"],
        "ciclos": summary["cycles"],
        "classes": summary["classes"]["total"],
        "lcom_aplicavel": summary["classes"]["applicable_lcom"],
        "lcom_na": summary["classes"]["not_applicable_lcom"],
        "cc_funcoes_producao": summary["complexity"]["functions_methods_production"],
        "halstead_zero_ratio": summary["halstead"]["zero_ratio"],
        "mi_diff_max": summary["maintainability"]["recomputation"]["max_abs_diff"],
        "saida": str(out),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
