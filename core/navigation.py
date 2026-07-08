"""
Navegação persistente — mantém a página ativa após F5/rerun.
Usa session_state + query_params (?page=) na URL.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from core.session_persistence import AUTH_QUERY_KEY, auth_query_params_extra

CURRENT_PAGE_KEY = "current_page"
QUERY_PAGE_KEY = "page"

PAGE_DASHBOARD = "dashboard"
PAGE_RESUMO = "resumo"
PAGE_CADASTRO = "cadastro"
PAGE_UPLOAD = "upload"
PAGE_MOTIVOS = "motivos"
PAGE_USUARIOS = "usuarios"
PAGE_CONSULTAR = "consultar"

PAGES: dict[str, dict[str, str]] = {
    PAGE_DASHBOARD: {
        "path": "pages/6_Dashboard.py",
        "label": "Dashboard",
    },
    PAGE_RESUMO: {
        "path": "pages/7_Resumo.py",
        "label": "Resumo",
    },
    PAGE_CADASTRO: {
        "path": "pages/2_Cadastro_Devolucao.py",
        "label": "Cadastro Devolução",
    },
    PAGE_UPLOAD: {
        "path": "pages/3_Upload_SAP.py",
        "label": "Upload Dados SAP",
    },
    PAGE_MOTIVOS: {
        "path": "pages/4_Config_Motivos.py",
        "label": "Configuração Motivos",
    },
    PAGE_USUARIOS: {
        "path": "pages/5_Usuarios.py",
        "label": "Usuários",
    },
    PAGE_CONSULTAR: {
        "path": "pages/1_Consultar_Devolucoes.py",
        "label": "Consultar Devoluções",
    },
}

DEFAULT_PAGE = PAGE_DASHBOARD


def _qp_value(key: str) -> Optional[str]:
    raw = st.query_params.get(key)
    if raw is None:
        return None
    if isinstance(raw, list):
        return str(raw[0]).strip() if raw else None
    return str(raw).strip() or None


def get_saved_page_slug() -> Optional[str]:
    slug = _qp_value(QUERY_PAGE_KEY) or st.session_state.get(CURRENT_PAGE_KEY)
    if slug and slug in PAGES:
        return slug
    return None


def set_current_page(slug: str) -> None:
    if slug not in PAGES:
        return
    st.session_state[CURRENT_PAGE_KEY] = slug
    if _qp_value(QUERY_PAGE_KEY) != slug:
        params: dict[str, Any] = {QUERY_PAGE_KEY: slug, **auth_query_params_extra()}
        st.query_params.from_dict(params)


def clear_navigation_state() -> None:
    st.session_state.pop(CURRENT_PAGE_KEY, None)
    for key in (QUERY_PAGE_KEY, AUTH_QUERY_KEY):
        if key in st.query_params:
            del st.query_params[key]


def register_page_view(slug: str) -> None:
    """Registra a página exibida (menu ou refresh na URL da página)."""
    set_current_page(slug)


def page_link_query(slug: str) -> dict[str, Any]:
    return {QUERY_PAGE_KEY: slug, **auth_query_params_extra()}


def route_authenticated_entry() -> None:
    """
    Entrada autenticada em app.py — restaura última tela ou abre o dashboard.
    """
    slug = get_saved_page_slug() or DEFAULT_PAGE
    set_current_page(slug)
    st.switch_page(PAGES[slug]["path"])
