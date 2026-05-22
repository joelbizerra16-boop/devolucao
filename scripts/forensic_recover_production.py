"""
Recuperacao forense — agrega TODAS as fontes SQLite locais + motivos.csv
e migra para Supabase APENAS registros reais faltantes (sem apagar/sobrescrever).

Nao migra devolucoes_legado (dados demo DEV-2026-xxxx).
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from database.connection import DATABASE_URL, is_postgres
from database.models import Base, Devolucao, Motivo, Usuario
from migrate_sqlite_to_supabase import (  # noqa: E402
    MIGRATION_PLAN,
    transform_devolucao,
    transform_motivo,
    transform_usuario,
)
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Fontes SQLite (mais recente / mais completa primeiro)
SQLITE_SOURCES = [
    ROOT / "data" / "devolucao.db",
    ROOT.parent / "FINALIZADO" / "projeto_devolucaoV01" / "data" / "devolucao.db",
    ROOT.parent / "FINALIZADO" / "projeto_devolucaoV02" / "data" / "devolucao.db",
    ROOT.parent / "FINALIZADO" / "projeto_devolucaoV03" / "data" / "devolucao.db",
    ROOT.parent / "FINALIZADO" / "projeto_devolucao" / "data" / "devolucao.db",
]

MOTIVOS_CSV = ROOT / "data" / "motivos.csv"
REPORT_JSON = ROOT / "logs" / "forensic_recovery_report.json"
REPORT_MD = ROOT / "logs" / "forensic_recovery_report.md"


def _read_sqlite_table(path: Path, table: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM [{table}] ORDER BY id")
        return [dict(r) for r in cur.fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def merge_by_id(sources: list[Path], table: str) -> dict[int, dict[str, Any]]:
    """Ultima fonte na lista sobrescreve — ordem: V01..V03 depois atual."""
    merged: dict[int, dict[str, Any]] = {}
    for path in reversed([p for p in sources if p.exists()]):
        for row in _read_sqlite_table(path, table):
            rid = row.get("id")
            if rid is not None:
                merged[int(rid)] = row
    return merged


def load_motivos_csv() -> list[dict[str, Any]]:
    if not MOTIVOS_CSV.exists():
        return []
    rows = []
    with MOTIVOS_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            desc = (row.get("descricao") or "").strip()
            if desc:
                rows.append({"id": i, "descricao": desc, "ativo": 1, "created_at": datetime.utcnow()})
    return rows


def pg_existing_ids(conn, table: str) -> set[int]:
    return {int(r[0]) for r in conn.execute(text(f'SELECT id FROM "{table}"'))}


def pg_existing_usernames(conn) -> set[str]:
    return {str(r[0]).lower() for r in conn.execute(text("SELECT username FROM usuarios"))}


def pg_existing_motivos_desc(conn) -> set[str]:
    return {str(r[0]).strip().lower() for r in conn.execute(text("SELECT LOWER(descricao) FROM motivos"))}


def pg_devolucao_fingerprint(conn) -> dict[int, str]:
    rows = conn.execute(text("SELECT id, nf_nfd, data_devolucao::text FROM devolucoes")).fetchall()
    return {int(r[0]): f"{r[1]}|{r[2]}" for r in rows}


def insert_missing(
    conn,
    table_name: str,
    sa_table: Any,
    records: list[dict],
    report: dict,
) -> int:
    if not records:
        return 0
    stmt = pg_insert(sa_table).values(records).on_conflict_do_nothing(index_elements=["id"])
    result = conn.execute(stmt)
    n = result.rowcount if result.rowcount and result.rowcount > 0 else len(records)
    report["migrated"][table_name] = report["migrated"].get(table_name, 0) + n
    return n


def insert_motivos_by_descricao(conn, records: list[dict], report: dict) -> int:
    existentes = pg_existing_motivos_desc(conn)
    novos = []
    for r in records:
        desc = str(r["descricao"]).strip()
        if desc.lower() not in existentes:
            item = {k: v for k, v in r.items() if k != "id"}
            item["descricao"] = desc
            novos.append(item)
    if not novos:
        return 0
    stmt = pg_insert(Motivo.__table__).values(novos).on_conflict_do_nothing(
        index_elements=["descricao"]
    )
    conn.execute(stmt)
    report["migrated"]["motivos_csv"] = len(novos)
    return len(novos)


def insert_usuarios_by_username(conn, records: list[dict], report: dict) -> int:
    existentes = pg_existing_usernames(conn)
    novos = [r for r in records if str(r["username"]).lower() not in existentes]
    if not novos:
        return 0
    # Sem preservar id se conflito — deixa PG gerar id
    for r in novos:
        r.pop("id", None)
    stmt = pg_insert(Usuario.__table__).values(novos)
    conn.execute(stmt)
    report["migrated"]["usuarios_novos_login"] = len(novos)
    return len(novos)


def reset_sequence(conn, table: str) -> None:
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


def run(dry_run: bool = False) -> dict:
    report: dict[str, Any] = {
        "sources": [str(p) for p in SQLITE_SOURCES if p.exists()],
        "merged_counts": {},
        "migrated": {},
        "skipped": {},
        "conflicts": [],
        "notes": [
            "devolucoes_legado NAO migrado (12 registros demo DEV-2026-xxxx).",
            "Nenhum SQLite local continha 8 usuarios; maximo 3 por arquivo.",
            "Nenhum SQLite local continha 35 devolucoes na tabela devolucoes; max 7 em V01.",
        ],
    }

    usuarios = merge_by_id(SQLITE_SOURCES, "usuarios")
    motivos = merge_by_id(SQLITE_SOURCES, "motivos")
    devolucoes = merge_by_id(SQLITE_SOURCES, "devolucoes")

    report["merged_counts"] = {
        "usuarios": len(usuarios),
        "motivos": len(motivos),
        "devolucoes": len(devolucoes),
        "motivos_csv": len(load_motivos_csv()),
    }

    if dry_run:
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        return report

    if not is_postgres():
        raise RuntimeError("DATABASE_URL PostgreSQL obrigatoria.")

    engine = create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require", "connect_timeout": 30},
    )
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        pg_u = pg_existing_ids(conn, "usuarios")
        pg_d = pg_existing_ids(conn, "devolucoes")
        pg_fp = pg_devolucao_fingerprint(conn)

        # --- Usuarios: inserir logins ausentes (sem forcar id conflitante) ---
        u_records = [transform_usuario(u) for u in usuarios.values()]
        insert_usuarios_by_username(conn, u_records, report)

        # --- Motivos SQLite por id ---
        m_sqlite = [transform_motivo(m) for m in motivos.values()]
        before_m = len(pg_existing_ids(conn, "motivos"))
        insert_missing(conn, "motivos", Motivo.__table__, m_sqlite, report)
        reset_sequence(conn, "motivos")

        # --- Motivos CSV (descricao unica) ---
        m_csv = [
            transform_motivo(m)
            for m in load_motivos_csv()
            if m.get("descricao")
        ]
        insert_motivos_by_descricao(conn, m_csv, report)

        # --- Devolucoes reais ---
        to_insert = []
        for did, raw in sorted(devolucoes.items()):
            rec = transform_devolucao(raw)
            if did in pg_d:
                fp_new = f"{rec.get('nf_nfd')}|{rec.get('data_devolucao')}"
                if pg_fp.get(did) != fp_new:
                    report["conflicts"].append(
                        {
                            "table": "devolucoes",
                            "id": did,
                            "postgres": pg_fp.get(did),
                            "sqlite": fp_new,
                            "action": "nao sobrescrito (id ja existe no Supabase)",
                        }
                    )
                continue
            to_insert.append(rec)

        if to_insert:
            insert_missing(conn, "devolucoes", Devolucao.__table__, to_insert, report)
        reset_sequence(conn, "devolucoes")

        report["final_counts"] = {
            t: conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
            for t in ("usuarios", "motivos", "devolucoes", "dados_sap")
        }

    engine.dispose()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    _write_md(report)
    return report


def _write_md(report: dict) -> None:
    lines = [
        "# Relatorio de Recuperacao Forense",
        "",
        f"**Gerado em:** {datetime.utcnow().isoformat()} UTC",
        "",
        "## Fontes analisadas",
        "",
    ]
    for s in report.get("sources", []):
        lines.append(f"- `{s}`")
    lines.append("")
    lines.append("## Registros agregados (SQLite real)")
    lines.append("")
    for k, v in report.get("merged_counts", {}).items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("## Migrados para Supabase")
    lines.append("")
    for k, v in report.get("migrated", {}).items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    if report.get("conflicts"):
        lines.append("## Conflitos (nao sobrescritos)")
        lines.append("")
        for c in report["conflicts"]:
            lines.append(f"- devolucao id={c['id']}: PG `{c['postgres']}` vs SQLite `{c['sqlite']}`")
    lines.append("")
    lines.append("## Contagem final Supabase")
    lines.append("")
    for k, v in report.get("final_counts", {}).items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("## Observacoes")
    lines.append("")
    for n in report.get("notes", []):
        lines.append(f"- {n}")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    dry = "--dry-run" in sys.argv
    print("=" * 70)
    print("RECUPERACAO FORENSE — DADOS REAIS")
    print("=" * 70)
    report = run(dry_run=dry)
    print(f"Fontes: {len(report.get('sources', []))}")
    print(f"Agregado: {report.get('merged_counts')}")
    if not dry:
        print(f"Migrado: {report.get('migrated')}")
        print(f"Conflitos: {len(report.get('conflicts', []))}")
        print(f"Final: {report.get('final_counts')}")
        print(f"Relatorio: {REPORT_MD}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
