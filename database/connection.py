"""
Conexão PostgreSQL (Supabase ou instância exclusiva) e fallback SQLite local.

SQLite só existe fora de production. Em production, DATABASE_URL PostgreSQL é obrigatória.
"""

from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from core.environment import (
    ProductionConfigError,
    database_url_raw,
    is_production,
    require_production_database_url,
    resolve_sslmode,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_PATH = DATA_DIR / "devolucao.db"


def _resolve_ipv6_hostname(host: str) -> str | None:
    """Resolve host Supabase (só AAAA) no Windows quando getaddrinfo falha."""
    try:
        infos = socket.getaddrinfo(host, 5432, socket.AF_INET6, socket.SOCK_STREAM)
        if infos:
            return infos[0][4][0]
    except OSError:
        pass

    if sys.platform == "win32":
        try:
            cmd = (
                f"(Resolve-DnsName -Name '{host}' -Type AAAA -ErrorAction SilentlyContinue "
                f"| Select-Object -ExpandProperty IPAddress -First 1)"
            )
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            ip = (proc.stdout or "").strip()
            if ip and ":" in ip:
                return ip
        except (OSError, subprocess.SubprocessError):
            pass
    return None


def _normalize_supabase_url(url: str) -> str:
    """Corrige URI comum do Supabase (porta, usuário pooler, IPv6 direto)."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not host:
        return url

    user = parsed.username or ""
    port = parsed.port
    project_ref = os.getenv("SUPABASE_PROJECT_REF", "").strip()

    # Host direto db.xxx.supabase.co — porta correta 5432 (não 6543)
    if host.startswith("db.") and host.endswith(".supabase.co"):
        if port in (None, 6543):
            port = 5432
        ipv6 = _resolve_ipv6_hostname(host)
        if ipv6:
            host = ipv6
            userinfo = ""
            if user:
                password = parsed.password or ""
                userinfo = f"{quote_plus(user)}:{quote_plus(password)}@" if password else f"{quote_plus(user)}@"
            netloc = f"{userinfo}[{host}]:{port}"
            return urlunparse(
                (
                    parsed.scheme,
                    netloc,
                    parsed.path or "/postgres",
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )

    # Pooler — usuário deve ser postgres.PROJECT_REF
    if "pooler.supabase.com" in host and user == "postgres" and project_ref:
        password = parsed.password or ""
        userinfo = f"{quote_plus(f'postgres.{project_ref}')}:{quote_plus(password)}@"
        netloc = f"{userinfo}{host}"
        if port:
            netloc += f":{port}"
        return urlunparse(
            (
                parsed.scheme,
                netloc,
                parsed.path or "/postgres",
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )

    return url


def _resolve_database_url() -> str:
    require_production_database_url()
    url = database_url_raw()
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if is_production() and not url.startswith("postgresql://"):
            raise ProductionConfigError(
                "DATABASE_URL em production deve ser PostgreSQL (postgresql://). "
                "SQLite é proibido em produção."
            )
        if url.startswith("postgresql"):
            url = _normalize_supabase_url(url)
        return url
    if is_production():
        raise ProductionConfigError(
            "DATABASE_URL é obrigatória quando DEVOLUCAO_ENV=production "
            "e está ausente ou vazia. A aplicação não inicia e não utiliza SQLite em produção."
        )
    return f"sqlite:///{DEFAULT_SQLITE_PATH}"


DATABASE_URL = _resolve_database_url()

# Registro do backend ativo (detecção de troca silenciosa SQLite ↔ PostgreSQL)
_LAST_LOGGED_BACKEND: str | None = None


def get_backend_label() -> str:
    if is_postgres():
        host = (urlparse(DATABASE_URL).hostname or "").lower()
        if "supabase" in host:
            return "PostgreSQL (Supabase)"
        return "PostgreSQL"
    return f"SQLite (local: {DEFAULT_SQLITE_PATH.name})"


def log_active_backend(force: bool = False) -> str:
    """Registra no log qual engine está ativa; alerta se o backend mudou."""
    global _LAST_LOGGED_BACKEND
    label = get_backend_label()
    if force or label != _LAST_LOGGED_BACKEND:
        try:
            from core.system_log import log_event

            if _LAST_LOGGED_BACKEND and _LAST_LOGGED_BACKEND != label:
                log_event(
                    "db",
                    f"ALERTA: backend alterado de {_LAST_LOGGED_BACKEND} para {label}",
                )
            log_event("db", f"Backend ativo: {label}")
        except Exception:
            pass
        _LAST_LOGGED_BACKEND = label
    return label


def is_postgres() -> bool:
    return DATABASE_URL.startswith("postgresql")


def _pool_kwargs() -> dict:
    return {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "300")),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_POOL_MAX_OVERFLOW", "10")),
    }


def postgres_connect_args() -> dict:
    return {
        "sslmode": resolve_sslmode(),
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
    }


def sqlalchemy_url(url: str) -> str:
    """Usa o driver psycopg2 já declarado em requirements.txt.

    SQLAlchemy 2.1 interpreta postgresql:// como psycopg 3, que não está instalado.
    A URL de ambiente permanece postgresql://; só a URL interna do engine muda.
    """
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


def _create_engine() -> Engine:
    pool = _pool_kwargs()
    if is_postgres():
        return create_engine(
            sqlalchemy_url(DATABASE_URL),
            **pool,
            connect_args=postgres_connect_args(),
        )
    return create_engine(
        DATABASE_URL,
        **pool,
        connect_args={"check_same_thread": False},
    )


engine = _create_engine()
log_active_backend(force=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_engine() -> Engine:
    return engine


def reset_engine() -> None:
    """Recria engine após falha de conexão (uso interno)."""
    global engine, SessionLocal, DATABASE_URL
    engine.dispose()
    DATABASE_URL = _resolve_database_url()
    engine = _create_engine()
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )
    log_active_backend(force=True)
