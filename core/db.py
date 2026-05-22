"""
Conexão global — delega engine/sessão para database.connection (Supabase PostgreSQL).
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Generator, Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from core.system_log import log_event

load_dotenv()


def get_database_url() -> str:
    from database.connection import DATABASE_URL

    return DATABASE_URL


def is_postgres() -> bool:
    from database.connection import is_postgres as _is_pg

    return _is_pg()


class DatabaseManager:
    """Singleton — sessões e health check sobre o engine compartilhado."""

    _instance: Optional[DatabaseManager] = None

    def __init__(self) -> None:
        self._session_factory: Optional[sessionmaker] = None
        self._last_health_ok: bool = False
        self._last_health_msg: str = ""

    @classmethod
    def instance(cls) -> DatabaseManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def engine(self) -> Engine:
        from database.connection import engine as conn_engine, SessionLocal

        if self._session_factory is None:
            self._session_factory = SessionLocal
            self._register_sqlite_pragma(conn_engine)
        return conn_engine

    @property
    def session_factory(self) -> sessionmaker:
        if self._session_factory is None:
            _ = self.engine
        assert self._session_factory is not None
        return self._session_factory

    def _register_sqlite_pragma(self, eng: Engine) -> None:
        if eng.dialect.name != "sqlite":
            return

        @event.listens_for(eng, "connect")
        def _pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    def reset(self, url: Optional[str] = None) -> None:
        from database import connection as conn_mod

        if url:
            os.environ["DATABASE_URL"] = url
            conn_mod.DATABASE_URL = url
            if url.startswith("postgres://"):
                conn_mod.DATABASE_URL = url.replace("postgres://", "postgresql://", 1)
        conn_mod.reset_engine()
        self._session_factory = None

    def check_connection(self, retries: int = 2) -> Tuple[bool, str]:
        ultimo_erro = "Conexão não testada."
        for tentativa in range(max(1, retries)):
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                backend = "PostgreSQL (Supabase)" if is_postgres() else "SQLite (local)"
                self._last_health_ok = True
                self._last_health_msg = f"Conexão OK — {backend}"
                return True, self._last_health_msg
            except SQLAlchemyError as exc:
                ultimo_erro = str(exc)
                log_event("db", f"Health check falhou (tentativa {tentativa + 1}): {exc}", exc)
                self.reset()
                time.sleep(0.4 * (tentativa + 1))
        self._last_health_ok = False
        self._last_health_msg = (
            "Não foi possível conectar ao banco de dados. "
            "Verifique DATABASE_URL no .env ou nos secrets do Streamlit Cloud."
        )
        if ultimo_erro:
            log_event("db", f"Detalhe técnico: {ultimo_erro}")
        return False, self._last_health_msg

    @contextmanager
    def session_scope(self, *, read_only: bool = False) -> Generator[Session, None, None]:
        from core.perf_monitor import track

        session = self.session_factory()
        try:
            with track("db", "session"):
                yield session
            if read_only:
                # Leitura pura: rollback expira atributos ORM → DetachedInstanceError
                if session.new or session.dirty or session.deleted:
                    session.rollback()
            elif session.new or session.dirty or session.deleted:
                session.commit()
            else:
                session.rollback()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def get_engine() -> Engine:
    return DatabaseManager.instance().engine


def get_session_factory() -> sessionmaker:
    return DatabaseManager.instance().session_factory


@contextmanager
def get_session(*, read_only: bool = True) -> Generator[Session, None, None]:
    """Sessão de leitura por padrão — sem commit em SELECT."""
    with DatabaseManager.instance().session_scope(read_only=read_only) as session:
        yield session


@contextmanager
def get_write_session() -> Generator[Session, None, None]:
    """Sessão para INSERT/UPDATE/DELETE."""
    with DatabaseManager.instance().session_scope(read_only=False) as session:
        yield session


def check_connection(retries: int = 2) -> Tuple[bool, str]:
    return DatabaseManager.instance().check_connection(retries=retries)


def reset_engine(url: Optional[str] = None) -> None:
    DatabaseManager.instance().reset(url=url)


def init_db() -> None:
    """Cria schema, índices e dados iniciais."""
    from database.migrations import run_migrations

    ok, msg = check_connection()
    if not ok:
        raise ConnectionError(msg)
    run_migrations()
