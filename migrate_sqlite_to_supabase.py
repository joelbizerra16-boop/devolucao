#!/usr/bin/env python3
"""
migrate_sqlite_to_supabase.py

Migra dados de data/devolucao.db (SQLite) para PostgreSQL/Supabase (DATABASE_URL).

- sqlite3: leitura somente do SQLite local
- SQLAlchemy + models do projeto: escrita no PostgreSQL
- Preserva IDs e timestamps
- Idempotente: ON CONFLICT (id) DO NOTHING (nao sobrescreve)

Uso:
    python migrate_sqlite_to_supabase.py
    python migrate_sqlite_to_supabase.py --dry-run
"""

from __future__ import annotations

import os
import sqlite3
import sys
import traceback
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from database.connection import DATABASE_URL, is_postgres  # noqa: E402
from database.models import Base, Devolucao, Motivo, Usuario  # noqa: E402

SQLITE_PATH = ROOT / "data" / "devolucao.db"

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
    try:
        return datetime.strptime(str(val).strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _norm_perfil(val: Any) -> str:
    p = str(val or "operador").strip().lower()
    return p if p in PERFIS_VALIDOS else "operador"


def _bool(val: Any) -> bool:
    return bool(val) if val is not None else False


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


MIGRATION_PLAN: list[tuple[str, Any, Callable[[dict[str, Any]], dict[str, Any]]]] = [
    ("usuarios", Usuario.__table__, transform_usuario),
    ("motivos", Motivo.__table__, transform_motivo),
    ("devolucoes", Devolucao.__table__, transform_devolucao),
]


def log(msg: str) -> None:
    print(msg, flush=True)


def read_sqlite(table: str) -> list[dict[str, Any]]:
    """Le registros do SQLite em modo somente leitura."""
    conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM [{table}] ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def existing_ids(conn: Connection, table_name: str) -> set[int]:
    result = conn.execute(text(f'SELECT id FROM "{table_name}"'))
    return {int(r[0]) for r in result if r[0] is not None}


def reset_sequence(conn: Connection, table_name: str) -> None:
    conn.execute(
        text(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', 'id'),
                COALESCE((SELECT MAX(id) FROM "{table_name}"), 1),
                true
            )
            """
        )
    )


def migrate_table(
    conn: Connection,
    table_name: str,
    sa_table: Any,
    transform: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Migra uma tabela; retorna estatisticas."""
    stats = {
        "table": table_name,
        "found": 0,
        "migrated": 0,
        "skipped": 0,
        "errors": [],
    }

    raw_rows = read_sqlite(table_name)
    stats["found"] = len(raw_rows)
    log(f"  [{table_name}] registros encontrados no SQLite: {stats['found']}")

    if stats["found"] == 0:
        return stats

    records = []
    for raw in raw_rows:
        try:
            records.append(transform(raw))
        except Exception as exc:
            stats["errors"].append(f"id={raw.get('id')}: {exc}")

    if stats["errors"]:
        for err in stats["errors"]:
            log(f"  [{table_name}] ERRO transformacao: {err}")

    before_ids = existing_ids(conn, table_name)
    to_insert = [r for r in records if r["id"] not in before_ids]
    stats["skipped"] = len(records) - len(to_insert)

    if not to_insert:
        log(f"  [{table_name}] nada novo para inserir (todos IDs ja existem no Supabase)")
        return stats

    try:
        stmt = pg_insert(sa_table).values(to_insert)
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        conn.execute(stmt)
        reset_sequence(conn, table_name)

        after_ids = existing_ids(conn, table_name)
        stats["migrated"] = len(after_ids - before_ids)
        log(f"  [{table_name}] registros migrados: {stats['migrated']}")
        log(f"  [{table_name}] registros ignorados (duplicados): {stats['skipped']}")
    except SQLAlchemyError as exc:
        stats["errors"].append(str(exc))
        log(f"  [{table_name}] ERRO SQL: {exc}")
        raise

    return stats


def validate(conn: Connection) -> bool:
    """Confirma que todos os IDs do SQLite existem no PostgreSQL."""
    ok = True
    for table_name, _, _ in MIGRATION_PLAN:
        sq_rows = read_sqlite(table_name)
        if not sq_rows:
            continue
        pg_ids = existing_ids(conn, table_name)
        missing = [r["id"] for r in sq_rows if r["id"] not in pg_ids]
        if missing:
            log(f"  VALIDACAO FALHA {table_name}: IDs ausentes no Supabase: {missing}")
            ok = False
    return ok


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    log("=" * 60)
    log("MIGRACAO SQLite -> Supabase")
    log("=" * 60)

    if not SQLITE_PATH.exists():
        log(f"ERRO: SQLite nao encontrado: {SQLITE_PATH}")
        return 1

    if not is_postgres():
        log("ERRO: DATABASE_URL deve apontar para PostgreSQL (Supabase).")
        log("       Defina DATABASE_URL no arquivo .env")
        return 1

    log(f"Origem SQLite: {SQLITE_PATH}")
    log(f"Destino: PostgreSQL (DATABASE_URL do .env)")
    log("")

    if dry_run:
        for table_name, _, _ in MIGRATION_PLAN:
            n = len(read_sqlite(table_name))
            log(f"  [dry-run] {table_name}: {n} registros")
        return 0

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"sslmode": "require", "connect_timeout": 30},
    )

    all_stats: list[dict[str, Any]] = []
    try:
        Base.metadata.create_all(bind=engine)

        with engine.begin() as conn:
            log("[1/3] Conectado ao SQLite (leitura) e PostgreSQL (escrita)")
            log("[2/3] Migrando tabelas...")
            log("")

            for table_name, sa_table, transform in MIGRATION_PLAN:
                log(f"--- {table_name} ---")
                try:
                    stats = migrate_table(conn, table_name, sa_table, transform)
                    all_stats.append(stats)
                except Exception:
                    log(f"  [{table_name}] FALHA CRITICA:")
                    log(traceback.format_exc())
                    return 1
                log("")

            log("[3/3] Validacao final...")
            if not validate(conn):
                return 1

    except Exception:
        log("ERRO de conexao ou migracao:")
        log(traceback.format_exc())
        return 1
    finally:
        engine.dispose()

    log("=" * 60)
    totals = {s["table"]: s["migrated"] for s in all_stats}
    u = totals.get("usuarios", 0)
    m = totals.get("motivos", 0)
    d = totals.get("devolucoes", 0)

    if u > 0 or any(s["found"] for s in all_stats if s["table"] == "usuarios"):
        log("OK usuarios migrados" + (f" ({u} novos)" if u else " (ja existiam)"))
    if m > 0 or any(s["found"] for s in all_stats if s["table"] == "motivos"):
        log("OK motivos migrados" + (f" ({m} novos)" if m else " (ja existiam)"))
    if d > 0 or any(s["found"] for s in all_stats if s["table"] == "devolucoes"):
        log("OK devolucoes migradas" + (f" ({d} novos)" if d else " (ja existiam)"))

    any_errors = any(s.get("errors") for s in all_stats)
    if any_errors:
        log("ATENCAO: houve erros parciais (ver logs acima)")
        return 1

    log("OK migracao concluida")
    log("=" * 60)
    log("")
    log("Proximo passo: streamlit run app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
