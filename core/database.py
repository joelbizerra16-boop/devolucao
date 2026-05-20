"""
Compatibilidade — reexporta camada database/ e core.db.
"""

from core.db import (
    check_connection,
    get_database_url,
    get_engine,
    get_session,
    init_db,
    is_postgres,
    reset_engine,
)
from database.connection import engine
from database.models import Base, Devolucao, Motivo, PerfilUsuario, StatusDevolucao, Usuario

__all__ = [
    "Base",
    "Devolucao",
    "Motivo",
    "PerfilUsuario",
    "StatusDevolucao",
    "Usuario",
    "check_connection",
    "engine",
    "get_database_url",
    "get_session",
    "init_db",
    "is_postgres",
    "reset_engine",
]
