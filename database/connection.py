"""
Conexão PostgreSQL Supabase — engine e sessões SQLAlchemy.
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
    url = (os.getenv("DATABASE_URL") or "").strip()
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql"):
            url = _normalize_supabase_url(url)
        return url
    return f"sqlite:///{DEFAULT_SQLITE_PATH}"


DATABASE_URL = _resolve_database_url()


def is_postgres() -> bool:
    return DATABASE_URL.startswith("postgresql")


def _create_engine() -> Engine:
    if is_postgres():
        return create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "sslmode": "require",
                "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
            },
        )
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"check_same_thread": False},
    )


engine = _create_engine()

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
