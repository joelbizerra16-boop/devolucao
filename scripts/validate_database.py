#!/usr/bin/env python3
"""Leitura do catálogo PostgreSQL para comparar origem e destino.

Não grava, não imprime senha, DATABASE_URL completa, hash ou segredo.
Não usa o fallback SQLite da aplicação.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.environment import resolve_sslmode
from core.redaction import redact_secrets
from database.connection import sqlalchemy_url

_IDENT = __import__("re").compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def configuration_error() -> str | None:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        return (
            "DATABASE_URL ausente ou vazia. "
            "Nenhuma leitura foi iniciada e o SQLite não é usado por este validador."
        )
    normalized = url
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized[len("postgres://") :]
    if not normalized.startswith("postgresql://"):
        return (
            "DATABASE_URL não é PostgreSQL. "
            "Este validador não aceita SQLite."
        )
    return None


def masked_target() -> str:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    parsed = urlparse(url)
    host = parsed.hostname or "?"
    port = parsed.port or ""
    db = (parsed.path or "").lstrip("/") or "?"
    user = parsed.username or "?"
    return f"postgresql://{user}:***@{host}:{port}/{db}"


def _safe(name: str) -> str:
    if not _IDENT.match(name):
        raise RuntimeError(f"Identificador SQL recusado: {name!r}")
    return name


def _engine() -> Engine:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return create_engine(
        sqlalchemy_url(url),
        pool_pre_ping=True,
        connect_args={
            "sslmode": resolve_sslmode(),
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
        },
    )


def _print_report(engine: Engine) -> None:
    print(f"backend: postgresql")
    print(f"alvo: {redact_secrets(masked_target())}")
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("SET default_transaction_read_only = on"))
        version = conn.execute(text("SELECT 1")).scalar()
        print(f"select_1: {version}")
        server = conn.execute(text("SHOW server_version")).scalar()
        print(f"server_version: {server}")

        insp = inspect(conn)
        tables = sorted(insp.get_table_names(schema="public"))
        print(f"tabelas: {len(tables)}")

        for table in tables:
            safe_table = _safe(table)
            columns = insp.get_columns(table, schema="public")
            names = [c["name"] for c in columns]
            count = conn.execute(text(f'SELECT COUNT(*) FROM public."{safe_table}"')).scalar()
            print(f"tabela {safe_table} registros={count}")
            if "id" in names:
                max_id = conn.execute(
                    text(f'SELECT MAX(id) FROM public."{safe_table}"')
                ).scalar()
                print(f"tabela {safe_table} max_id={max_id}")

        date_rows = conn.execute(
            text(
                """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND data_type IN (
                    'date',
                    'timestamp without time zone',
                    'timestamp with time zone'
                  )
                ORDER BY table_name, column_name
                """
            )
        ).fetchall()
        for table_name, column_name in date_rows:
            safe_table = _safe(str(table_name))
            safe_column = _safe(str(column_name))
            row = conn.execute(
                text(
                    f'SELECT MIN("{safe_column}"), MAX("{safe_column}") '
                    f'FROM public."{safe_table}"'
                )
            ).one()
            print(
                f"tabela {safe_table} coluna {safe_column} "
                f"min={row[0]} max={row[1]}"
            )

        sequences = conn.execute(
            text(
                """
                SELECT schemaname, sequencename, last_value
                FROM pg_sequences
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, sequencename
                """
            )
        ).fetchall()
        print(f"sequences: {len(sequences)}")
        for schema, name, last_value in sequences:
            print(f"sequence {schema}.{name} last_value={last_value}")


def main() -> int:
    load_dotenv()
    error = configuration_error()
    if error:
        print(error, file=sys.stderr)
        return 1
    engine = _engine()
    try:
        _print_report(engine)
    except Exception as exc:
        print(redact_secrets(str(exc)), file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
