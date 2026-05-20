"""Controle de permissões — VISITANTE x ADMINISTRADOR."""

from __future__ import annotations

import streamlit as st

from core.auth import get_current_user, require_auth
from core.constants import (
    LABEL_ADMIN,
    LABEL_VISITANTE,
    MAPA_DB_PARA_LABEL,
    MAPA_LABEL_PARA_DB,
    PERFIS_COMBO,
    PERFIS_VALIDOS,
    PERFIL_ADMIN_DB,
    PERFIL_VISITANTE_DB,
    PERFIL_LABELS,
    label_para_perfil,
    perfil_para_label,
)

__all__ = [
    "LABEL_ADMIN",
    "LABEL_VISITANTE",
    "PERFIS_COMBO",
    "PERFIS_VALIDOS",
    "PERFIL_ADMIN_DB",
    "PERFIL_VISITANTE_DB",
    "PERFIL_LABELS",
    "MAPA_DB_PARA_LABEL",
    "MAPA_LABEL_PARA_DB",
    "perfil_para_label",
    "label_para_perfil",
    "is_administrador",
    "is_visitante",
    "pode_editar",
    "exigir_administrador",
    "aviso_somente_leitura",
]


def is_administrador() -> bool:
    user = get_current_user()
    if user is None:
        return False
    return user.perfil == PERFIL_ADMIN_DB


def is_visitante() -> bool:
    return not is_administrador()


def pode_editar() -> bool:
    return is_administrador()


def exigir_administrador() -> None:
    """Bloqueia página/ação exclusiva de administrador."""
    require_auth()
    if not is_administrador():
        st.warning("Usuário sem permissão.")
        st.stop()


def aviso_somente_leitura() -> None:
    """Exibe aviso para perfil visitante (não interrompe a página)."""
    if is_visitante():
        st.info("Perfil **VISITANTE** — acesso somente leitura.")
