"""
Migração segura SQLite → PostgreSQL/Supabase.
- Preserva IDs, timestamps e relacionamentos lógicos
- Não apaga tabelas, não trunca, não sobrescreve registros existentes
- Idempotente: ON CONFLICT (id) DO NOTHING
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

SQLITE_PATH = ROOT / "data" / "devolucao.db"

# Ordem: sem FKs entre tabelas principais
MIGRATION_ORDER = (
    ("usuarios", "usuarios"),
    ("motivos", "motivos"),
    ("devolucoes", "devolucoes"),
    ("dados_sap", "dados_sap"),
)

PERFIS_VALIDOS = {"admin", "operador", "supervisor", "visualizador"}


def _parse_dt(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time())
    s = str(val).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:26], fmt)
        except ValueError:
            continue
    return None


def _parse_date(val: Any) -> date | None:
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()[:10]
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def _norm_perfil(val: Any) -> str:
    if val is None:
        return "operador"
    p = str(val).strip().lower()
    return p if p in PERFIS_VALIDOS else "operador"


def _bool(val: Any) -> bool:
    return bool(val) if val is not None else False


def sqlite_rows(table: str) -> tuple[list[str], list[tuple]]:
    conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM [{table}] ORDER BY id")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description] if cur.description else []
    conn.close()
    return cols, [tuple(r[c] for c in cols) for r in rows]


def row_to_dict(cols: list[str], row: tuple) -> dict[str, Any]:
    return dict(zip(cols, row))


def transform_usuario(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": d["id"],
        "username": d["username"],
        "senha_hash": d["senha_hash"],
        "nome": d["nome"],
        "email": d.get("email"),
        "perfil": _norm_perfil(d.get("perfil")),
        "ativo": _bool(d.get("ativo")),
        "empresa_id": d.get("empresa_id"),
        "created_at": _parse_dt(d.get("created_at")) or datetime.utcnow(),
        "updated_at": _parse_dt(d.get("updated_at")) or datetime.utcnow(),
    }


def transform_motivo(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": d["id"],
        "descricao": d["descricao"],
        "ativo": _bool(d.get("ativo")),
        "created_at": _parse_dt(d.get("created_at")) or datetime.utcnow(),
    }


def transform_devolucao(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": d["id"],
        "data_lancamento": _parse_date(d["data_lancamento"]),
        "usuario": d["usuario"],
        "usuario_ultima_edicao": d.get("usuario_ultima_edicao"),
        "data_devolucao": _parse_date(d["data_devolucao"]),
        "data_emissao_nf": _parse_date(d.get("data_emissao_nf")),
        "nf_nfd": d.get("nf_nfd"),
        "cod_cliente": d.get("cod_cliente"),
        "cliente": d.get("cliente"),
        "vendedor": d.get("vendedor"),
        "valor_nf": d.get("valor_nf"),
        "cidade": d.get("cidade"),
        "bairro": d.get("bairro"),
        "motivo_devolucao": d["motivo_devolucao"],
        "observacao": d.get("observacao"),
        "created_at": _parse_dt(d.get("created_at")) or datetime.utcnow(),
        "updated_at": _parse_dt(d.get("updated_at")) or datetime.utcnow(),
    }


def transform_dados_sap(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": d["id"],
        "nf_nfd": d["nf_nfd"],
        "data_emissao_nf": _parse_date(d.get("data_emissao_nf")),
        "cod_cliente": d.get("cod_cliente"),
        "cliente": d.get("cliente"),
        "cidade": d.get("cidade"),
        "bairro": d.get("bairro"),
        "vendedor": d.get("vendedor"),
        "valor_nf": d.get("valor_nf"),
        "arquivo_origem": d.get("arquivo_origem"),
        "data_importacao": _parse_dt(d.get("data_importacao")) or datetime.utcnow(),
    }


TRANSFORMERS = {
    "usuarios": transform_usuario,
    "motivos": transform_motivo,
    "devolucoes": transform_devolucao,
    "dados_sap": transform_dados_sap,
}


def ensure_postgres_schema() -> None:
    from database.models import Base
    from database.connection import engine, is_postgres

    if not is_postgres():
        raise RuntimeError("DATABASE_URL deve apontar para PostgreSQL/Supabase.")
    Base.metadata.create_all(bind=engine)


def upsert_batch(conn, table, records: list[dict], batch_size: int = 200) -> tuple[int, int]:
    from sqlalchemy import Table, MetaData
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    if not records:
        return 0, 0

    meta = MetaData()
    tbl = Table(table, meta, autoload_with=conn)
    inserted = 0
    skipped = 0

    for i in range(0, len(records), batch_size):
        chunk = records[i : i + batch_size]
        stmt = pg_insert(tbl).values(chunk)
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        result = conn.execute(stmt)
        # rowcount pode ser -1 em alguns drivers; estimamos pelo chunk
        inserted += result.rowcount if result.rowcount and result.rowcount > 0 else 0

    # Contagem real pós-migração
    from sqlalchemy import text

    total_pg = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    return total_pg, len(records)


def reset_sequence(conn, table: str) -> None:
    from sqlalchemy import text

    conn.execute(
        text(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', 'id'),
                COALESCE((SELECT MAX(id) FROM "{table}"), 1),
                true
            )
            """
        )
    )


def count_sqlite(table: str) -> int:
    conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM [{table}]")
    n = cur.fetchone()[0]
    conn.close()
    return n


def count_postgres(conn, table: str) -> int:
    from sqlalchemy import text

    return conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()


def migrate(dry_run: bool = False) -> bool:
    if not SQLITE_PATH.exists():
        print(f"ERRO: SQLite não encontrado: {SQLITE_PATH}")
        return False

    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url.startswith(("postgresql", "postgres")):
        print("ERRO: DATABASE_URL PostgreSQL obrigatória para migração.")
        return False

    from sqlalchemy import create_engine, text
    from database.connection import DATABASE_URL

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    print("=" * 60)
    print("MIGRACAO SQLite -> Supabase")
    print("=" * 60)
    print(f"Origem: {SQLITE_PATH} ({SQLITE_PATH.stat().st_size:,} bytes)")
    print(f"Destino: PostgreSQL (pooler Supabase)")
    print()

    if dry_run:
        for table, _ in MIGRATION_ORDER:
            print(f"  [dry-run] {table}: {count_sqlite(table)} registros no SQLite")
        return True

    ensure_postgres_schema()

    eng = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"sslmode": "require", "connect_timeout": 30},
    )

    ok = True
    with eng.begin() as conn:
        for sqlite_table, pg_table in MIGRATION_ORDER:
            if count_sqlite(sqlite_table) == 0:
                print(f"  {pg_table}: SQLite vazio — pulando")
                continue

            cols, rows = sqlite_rows(sqlite_table)
            transformer = TRANSFORMERS[pg_table]
            records = [transformer(row_to_dict(cols, r)) for r in rows]
            before = count_postgres(conn, pg_table)
            print(f"  Migrando {pg_table}: {len(records)} do SQLite (PG antes: {before})...")

            from sqlalchemy.dialects.postgresql import insert as pg_insert
            from sqlalchemy import Table, MetaData

            meta = MetaData()
            tbl = Table(pg_table, meta, autoload_with=conn)
            batch_size = 500 if pg_table == "dados_sap" else 50
            for i in range(0, len(records), batch_size):
                chunk = records[i : i + batch_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing(
                    index_elements=["id"]
                )
                conn.execute(stmt)

            reset_sequence(conn, pg_table)
            after = count_postgres(conn, pg_table)
            sq = count_sqlite(sqlite_table)
            match = "OK" if after >= sq else "DIVERGÊNCIA"
            print(f"    PG depois: {after} | SQLite: {sq} | {match}")
            if after < sq:
                ok = False

    print()
    print("[VALIDAÇÃO FINAL]")
    with eng.connect() as conn:
        for _, pg_table in MIGRATION_ORDER:
            sq = count_sqlite(pg_table) if SQLITE_PATH.exists() else 0
            pg = count_postgres(conn, pg_table)
            status = "OK" if pg >= sq else "FALHA"
            print(f"  [{status}] {pg_table}: SQLite={sq} PostgreSQL={pg}")

    eng.dispose()
    print("=" * 60)
    return ok


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    success = migrate(dry_run=dry)
    sys.exit(0 if success else 1)
