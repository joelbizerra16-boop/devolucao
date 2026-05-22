"""
Migrations — criação de tabelas, índices PostgreSQL e seeds iniciais.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text

from core.db import get_engine, get_session, is_postgres
from core.paths import MOTIVOS_PADRAO
from core.system_log import log_event
from database.models import Base, Motivo, PerfilUsuario, Usuario
from database.schema_compat import assert_usuarios_postgres_schema
import bcrypt

from core.constants import USUARIO_PROTEGIDO


def _hash_password(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _criar_indices_postgres() -> None:
    if not is_postgres():
        return
    engine = get_engine()
    indices = [
        "CREATE INDEX IF NOT EXISTS ix_devolucoes_data_devolucao ON devolucoes (data_devolucao)",
        "CREATE INDEX IF NOT EXISTS ix_devolucoes_nf_nfd ON devolucoes (nf_nfd)",
        "CREATE INDEX IF NOT EXISTS ix_devolucoes_cod_cliente ON devolucoes (cod_cliente)",
        "CREATE INDEX IF NOT EXISTS ix_devolucoes_motivo ON devolucoes (motivo_devolucao)",
        "CREATE INDEX IF NOT EXISTS ix_devolucoes_created_at ON devolucoes (created_at)",
        "CREATE INDEX IF NOT EXISTS ix_usuarios_username ON usuarios (username)",
        "CREATE INDEX IF NOT EXISTS ix_motivos_descricao ON motivos (descricao)",
        "CREATE INDEX IF NOT EXISTS ix_motivos_ativo ON motivos (ativo)",
    ]
    with engine.begin() as conn:
        for ddl in indices:
            conn.execute(text(ddl))


def _migrar_sqlite_legado() -> None:
    if is_postgres():
        return
    engine = get_engine()
    with engine.connect() as conn:
        tabelas = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }
        if "devolucoes" not in tabelas:
            return
        colunas = {row[1] for row in conn.execute(text("PRAGMA table_info(devolucoes)"))}
        if "data_lancamento" in colunas:
            return
        if "devolucoes_legado" not in tabelas:
            conn.execute(text("ALTER TABLE devolucoes RENAME TO devolucoes_legado"))
            conn.commit()


def _migrar_colunas_sqlite() -> None:
    if is_postgres():
        return
    engine = get_engine()
    with engine.connect() as conn:
        tabelas = {
            row[0]
            for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
        if "devolucoes" not in tabelas:
            return
        existentes = {row[1] for row in conn.execute(text("PRAGMA table_info(devolucoes)"))}
        alterou = False
        if "cliente" not in existentes:
            conn.execute(text("ALTER TABLE devolucoes ADD COLUMN cliente VARCHAR(200)"))
            alterou = True
        if "usuario_ultima_edicao" not in existentes:
            conn.execute(
                text("ALTER TABLE devolucoes ADD COLUMN usuario_ultima_edicao VARCHAR(120)")
            )
            alterou = True
        if alterou:
            conn.commit()


def seed_motivos_padrao() -> None:
    with get_session() as session:
        qtd = session.query(Motivo).count()
        if qtd > 0:
            return
        for desc in MOTIVOS_PADRAO:
            session.add(Motivo(descricao=desc.strip(), ativo=True))
        log_event("db", f"Seed: {len(MOTIVOS_PADRAO)} motivos padrão.")


def seed_usuario_admin() -> None:
    with get_session() as session:
        existe = (
            session.query(Usuario)
            .filter(Usuario.username == USUARIO_PROTEGIDO)
            .first()
        )
        if existe:
            return
        session.add(
            Usuario(
                nome="Administrador",
                username=USUARIO_PROTEGIDO,
                senha_hash=_hash_password("admin123"),
                perfil=PerfilUsuario.ADMIN,
                ativo=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        log_event("db", "Seed: usuário admin padrão criado.")


def run_migrations() -> None:
    try:
        _migrar_sqlite_legado()
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        assert_usuarios_postgres_schema(engine)
        _migrar_colunas_sqlite()
        _criar_indices_postgres()
        seed_motivos_padrao()
        seed_usuario_admin()
    except Exception as exc:
        log_event("sql", f"run_migrations falhou: {exc}", exc)
        raise
