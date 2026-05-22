"""
Relatório forense READ-ONLY — SQLite vs PostgreSQL.
Não altera, não trunca, não recria schema.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

SQLITE_PATH = ROOT / "data" / "devolucao.db"
TABLES = ("usuarios", "motivos", "devolucoes", "dados_sap")


def mask_url(url: str) -> str:
    p = urlparse(url)
    user = p.username or ""
    host = p.hostname or "(local)"
    db = (p.path or "").lstrip("/") or str(SQLITE_PATH.name)
    return f"{p.scheme}://{user[:3]}***@{host}:{p.port or ''}/{db}"


def sqlite_counts() -> dict:
    if not SQLITE_PATH.exists():
        return {"error": f"Arquivo não encontrado: {SQLITE_PATH}"}
    conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [r[0] for r in cur.fetchall()]
    counts = {}
    for t in all_tables:
        cur.execute(f"SELECT COUNT(*) FROM [{t}]")
        counts[t] = cur.fetchone()[0]
    samples = {}
    for t in TABLES:
        if t not in all_tables:
            continue
        cur.execute(f"PRAGMA table_info([{t}])")
        col_names = {c[1] for c in cur.fetchall()}
        samples[t] = {"columns": sorted(col_names)}
        cur.execute(f"SELECT MAX(id) FROM [{t}]")
        samples[t]["max_id"] = cur.fetchone()[0]
        if "created_at" in col_names:
            cur.execute(f"SELECT MAX(created_at) FROM [{t}]")
            samples[t]["max_created_at"] = cur.fetchone()[0]
        if t == "usuarios" and "username" in col_names:
            cur.execute("SELECT id, username, nome FROM usuarios LIMIT 8")
            samples[t]["sample"] = cur.fetchall()
    conn.close()
    return {
        "path": str(SQLITE_PATH),
        "size_bytes": SQLITE_PATH.stat().st_size,
        "modified": datetime.fromtimestamp(SQLITE_PATH.stat().st_mtime).isoformat(),
        "tables": all_tables,
        "counts": counts,
        "samples": samples,
    }


def postgres_counts() -> dict:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        return {"error": "DATABASE_URL não definida — sistema usaria SQLite fallback"}
    if not url.startswith(("postgresql", "postgres")):
        return {"error": f"DATABASE_URL não é PostgreSQL: {mask_url(url)}"}
    try:
        from sqlalchemy import create_engine, inspect, text
    except ImportError:
        return {"error": "sqlalchemy não instalado no Python atual"}

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    eng = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"sslmode": "require", "connect_timeout": 10},
    )
    result = {"url_masked": mask_url(url), "connected": False}
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
            result["connected"] = True
            insp = inspect(eng)
            all_tables = insp.get_table_names()
            result["tables"] = all_tables
            counts = {}
            for t in all_tables:
                counts[t] = conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
            result["counts"] = counts
            samples = {}
            for t in TABLES:
                if t not in all_tables:
                    continue
                mx_id = conn.execute(text(f'SELECT MAX(id) FROM "{t}"')).scalar()
                samples[t] = {"max_id": mx_id}
                try:
                    mx_ca = conn.execute(text(f'SELECT MAX(created_at) FROM "{t}"')).scalar()
                    samples[t]["max_created_at"] = str(mx_ca) if mx_ca else None
                except Exception:
                    pass
            result["samples"] = samples
    except Exception as exc:
        result["error"] = str(exc)
    finally:
        eng.dispose()
    return result


def main() -> None:
    print("=" * 60)
    print("RELATÓRIO FORENSE — DEVOLUÇÃO")
    print("=" * 60)

    url_env = (os.getenv("DATABASE_URL") or "").strip()
    active = url_env if url_env else f"sqlite:///{SQLITE_PATH}"
    print("\n[ETAPA 1] Conexão ativa (resolvida pelo código)")
    print("  DATABASE_URL definida:", bool(url_env))
    print("  URL mascarada:", mask_url(active))
    print("  Provider:", "PostgreSQL" if active.startswith("postgresql") else "SQLite")

    print("\n[ETAPA 2] SQLite local (READ-ONLY)")
    sq = sqlite_counts()
    if "error" in sq:
        print("  ERRO:", sq["error"])
    else:
        print(f"  Arquivo: {sq['path']}")
        print(f"  Tamanho: {sq['size_bytes']:,} bytes | Modificado: {sq['modified']}")
        for t in TABLES:
            n = sq["counts"].get(t, "—")
            print(f"  {t}: {n}")
        if sq.get("samples"):
            print("  Amostras:", sq["samples"])

    print("\n[ETAPA 3] PostgreSQL/Supabase")
    pg = postgres_counts()
    if "error" in pg and not pg.get("connected"):
        print("  ", pg["error"])
    elif pg.get("connected"):
        print("  Conectado:", pg["url_masked"])
        for t in TABLES:
            n = pg.get("counts", {}).get(t, "—")
            print(f"  {t}: {n}")
        print("  Amostras:", pg.get("samples", {}))
    else:
        print("  ", pg.get("error", pg))

    print("\n[ETAPA 4] Veredito")
    sq_total = sum(sq.get("counts", {}).get(t, 0) for t in TABLES) if "counts" in sq else 0
    pg_total = sum(pg.get("counts", {}).get(t, 0) for t in TABLES) if pg.get("connected") else 0
    if sq_total > 0 and pg_total == 0:
        print("  DADOS REAIS: SQLite local")
        print("  CAUSA PROVÁVEL: DATABASE_URL ativa aponta para Supabase vazio")
    elif pg_total > 0 and sq_total == 0:
        print("  DADOS REAIS: PostgreSQL/Supabase")
    elif sq_total > 0 and pg_total > 0:
        print("  DADOS EM AMBOS — comparar timestamps antes de migrar")
    else:
        print("  NENHUM banco com dados operacionais encontrados")
    print("=" * 60)


if __name__ == "__main__":
    main()
