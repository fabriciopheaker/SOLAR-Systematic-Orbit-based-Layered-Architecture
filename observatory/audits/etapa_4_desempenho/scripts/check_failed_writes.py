"""Verifica se respostas 500 deixaram usuários gravados no SQLite."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "dados"
CONSOLIDATED = DATA / "RESULTADOS_CONSOLIDADOS.json"
RAW = DATA / "RESULTADOS_BRUTOS"
DB = DATA / "tmp" / "bench.sqlite"

data = json.loads(CONSOLIDATED.read_text(encoding="utf-8"))
run_id = data["run_id"]
connection = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

for scenario in ("C_create_c2", "C_create_c4"):
    path = RAW / f"{scenario}.csv"
    if not path.exists():
        continue
    rows = [
        row for row in csv.DictReader(path.open(encoding="utf-8"))
        if row["status"] == "500"
    ]
    print(f"{scenario}: {len(rows)} respostas 500")
    for row in rows:
        email = f"bench-{run_id}-{scenario}-{row['seq']}@example.com".lower()
        count = connection.execute(
            "SELECT COUNT(*) FROM users WHERE email_user = ?", (email,)
        ).fetchone()[0]
        if count:
            print(f"  seq={row['seq']} GRAVADO apesar do 500")
