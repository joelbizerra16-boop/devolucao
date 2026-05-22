"""
Relatório forense completo — SQLite local vs Supabase.
Somente leitura no SQLite; leitura no PostgreSQL.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

SQLITE_PATH = ROOT / "data" / "devolucao.db"
CORE_TABLES = (
    "usuarios",
    "motivos",
    "devolucoes",
    "dados_sap",
    "historico_devolucoes",
    "devolucoes_legado",
    "auditoria_logs",
)


def sqlite_full_audit() -> dict:
    if not SQLITE_PATH.exists():
        return {"error": str(SQLITE_PATH)}

    conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]

    audit = {
        "path": str(SQLITE_PATH),
        "size_bytes": SQLITE_PATH.stat().st_size,
        "modified": datetime.fromtimestamp(SQLITE_PATH.stat().st_mtime).isoformat(),
        "tables": {},
    }

    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM [{t}]")
        count = cur.fetchone()[0]
        cur.execute(f"PRAGMA table_info([{t}])")
        cols = [c[1] for c in cur.fetchall()]
        entry = {"count": count, "columns": cols}
        if count and "id" in cols:
            cur.execute(f"SELECT MIN(id), MAX(id) FROM [{t}]")
            mn, mx = cur.fetchone()
            entry["id_range"] = [mn, mx]
        if count and "created_at" in cols:
            cur.execute(f"SELECT MIN(created_at), MAX(created_at) FROM [{t}]")
            entry["created_range"] = cur.fetchone()
        audit["tables"][t] = entry

    # Amostras detalhadas
    samples = {}
    if "usuarios" in tables:
        cur.execute("SELECT id, username, nome, perfil, ativo, created_at FROM usuarios ORDER BY id")
        samples["usuarios"] = [dict(r) for r in cur.fetchall()]

    for t in ("devolucoes", "devolucoes_legado", "historico_devolucoes"):
        if t not in tables:
            continue
        cur.execute(f"PRAGMA table_info([{t}])")
        cols = [c[1] for c in cur.fetchall()]
        order = "id" if "id" in cols else "rowid"
        sel = ", ".join(cols[:12])
        cur.execute(f"SELECT {sel} FROM [{t}] ORDER BY {order}")
        samples[t] = [dict(r) for r in cur.fetchall()]

    if "motivos" in tables:
        cur.execute("SELECT id, descricao, ativo FROM motivos ORDER BY id")
        samples["motivos"] = [dict(r) for r in cur.fetchall()]

    if "auditoria_logs" in tables:
        cur.execute("SELECT * FROM auditoria_logs LIMIT 20")
        samples["auditoria_logs"] = [dict(r) for r in cur.fetchall()]

    conn.close()
    audit["samples"] = samples
    return audit


def postgres_audit() -> dict:
    import os

    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url.startswith(("postgresql", "postgres")):
        return {"error": "DATABASE_URL ausente"}

    from sqlalchemy import create_engine, inspect, text

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    eng = create_engine(url, connect_args={"sslmode": "require", "connect_timeout": 15})
    out = {"connected": False, "tables": {}, "samples": {}}
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
            out["connected"] = True
            insp = inspect(eng)
            for t in insp.get_table_names():
                out["tables"][t] = conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()

            for t in CORE_TABLES:
                if t not in out["tables"]:
                    continue
                try:
                    rows = conn.execute(
                        text(f'SELECT id FROM "{t}" ORDER BY id')
                    ).fetchall()
                    out["samples"][f"{t}_ids"] = [r[0] for r in rows]
                except Exception:
                    pass

            if "usuarios" in out["tables"]:
                rows = conn.execute(
                    text("SELECT id, username, nome, perfil, ativo FROM usuarios ORDER BY id")
                ).fetchall()
                out["samples"]["usuarios"] = [
                    {"id": r[0], "username": r[1], "nome": r[2], "perfil": r[3], "ativo": r[4]}
                    for r in rows
                ]
    except Exception as exc:
        out["error"] = str(exc)
    finally:
        eng.dispose()
    return out


def compare_missing(sq: dict, pg: dict) -> dict:
    cmp = {}
    sq_ids = sq.get("samples", {})
    pg_ids = pg.get("samples", {})

    for key, table in (
        ("usuarios", "usuarios"),
        ("motivos", "motivos"),
        ("devolucoes", "devolucoes"),
    ):
        legacy_keys = []
        if table == "devolucoes":
            legacy_keys = ["devolucoes_legado", "historico_devolucoes"]

        sqlite_all_ids = set()
        if f"{table}_ids" in sq_ids:
            sqlite_all_ids.update(sq_ids[f"{table}_ids"])
        for lk in legacy_keys:
            for row in sq.get("samples", {}).get(lk, []):
                if "id" in row:
                    sqlite_all_ids.add(row["id"])

        pg_set = set(pg_ids.get(f"{table}_ids", []))
        missing_in_pg = sorted(sqlite_all_ids - pg_set)
        only_pg = sorted(pg_set - sqlite_all_ids)
        cmp[table] = {
            "sqlite_ids": sorted(sqlite_all_ids),
            "postgres_ids": sorted(pg_set),
            "missing_in_postgres": missing_in_pg,
            "only_in_postgres": only_pg,
        }

    # Contagens legado
    for lk in ("devolucoes_legado", "historico_devolucoes"):
        rows = sq.get("samples", {}).get(lk, [])
        cmp[lk] = {"count": len(rows), "ids": [r.get("id") for r in rows if "id" in r]}

    return cmp


def main() -> None:
    print("=" * 70)
    print("RELATORIO FORENSE — RECUPERACAO DE DADOS")
    print("=" * 70)

    sq = sqlite_full_audit()
    pg = postgres_audit()
    cmp = compare_missing(sq, pg) if "error" not in sq and pg.get("connected") else {}

    report = {"sqlite": sq, "postgres": pg, "comparison": cmp, "generated_at": datetime.utcnow().isoformat()}

    out_path = ROOT / "logs" / "forensic_recovery_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    print(f"\nSQLite: {sq.get('path')}")
    print(f"  Tamanho: {sq.get('size_bytes', 0):,} bytes | Modificado: {sq.get('modified')}")
    print("\n  TABELAS:")
    for t, info in sorted(sq.get("tables", {}).items()):
        print(f"    {t}: {info.get('count')} registros | cols={len(info.get('columns', []))}")

    if pg.get("connected"):
        print("\nPostgreSQL (Supabase):")
        for t in CORE_TABLES:
            if t in pg.get("tables", {}):
                print(f"    {t}: {pg['tables'][t]}")

    print("\nCOMPARACAO (IDs faltando no Supabase):")
    for t, c in cmp.items():
        if "missing_in_postgres" in c:
            print(f"  {t}: SQLite={len(c['sqlite_ids'])} PG={len(c['postgres_ids'])} faltam={c['missing_in_postgres']}")

    print(f"\nRelatorio JSON: {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
