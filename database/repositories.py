"""
Fachada de repositórios — acesso unificado ao PostgreSQL (Supabase).
"""

from __future__ import annotations

from repositories import (
    dashboard_repository,
    devolucao_repository,
    motivo_repository,
    sap_repository,
    usuario_repository,
)

__all__ = [
    "dashboard_repository",
    "devolucao_repository",
    "motivo_repository",
    "sap_repository",
    "usuario_repository",
]
