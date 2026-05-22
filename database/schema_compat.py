"""
Compatibilidade de schema — login em usuarios usa coluna ``username`` (PostgreSQL/Supabase).

A coluna ``usuario`` existe apenas em ``devolucoes`` (responsável pela devolução).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from core.system_log import log_event
from database.connection import is_postgres

# Nome real no PostgreSQL / Supabase
USUARIOS_LOGIN_COLUMN = "username"

# Alias legado em código antigo (não é coluna SQL em usuarios)
USUARIOS_LOGIN_LEGACY_ATTR = "usuario"


def username_from_entity(user: Any) -> str:
    """Extrai login de ORM, dict ou SimpleNamespace (suporta chave legada ``usuario``)."""
    if user is None:
        return ""
    if isinstance(user, dict):
        return str(user.get("username") or user.get("usuario") or "").strip().lower()
    login = getattr(user, "username", None) or getattr(user, "usuario", None)
    return str(login or "").strip().lower()


def assert_usuarios_postgres_schema(engine: Engine) -> None:
    """
    Garante que a tabela usuarios no PostgreSQL expõe ``username``.
    Não altera tabelas — apenas valida e registra alertas.
    """
    if not is_postgres():
        return

    insp = inspect(engine)
    if "usuarios" not in insp.get_table_names():
        return

    colunas = {c["name"] for c in insp.get_columns("usuarios")}

    if USUARIOS_LOGIN_COLUMN not in colunas:
        raise RuntimeError(
            f"Schema invalido: tabela usuarios sem coluna '{USUARIOS_LOGIN_COLUMN}'. "
            f"Colunas encontradas: {sorted(colunas)}"
        )

    if USUARIOS_LOGIN_LEGACY_ATTR in colunas:
        log_event(
            "db",
            "ALERTA: tabela usuarios possui coluna legada 'usuario' e 'username'. "
            "O ORM usa apenas 'username' para login.",
        )
