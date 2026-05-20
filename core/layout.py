"""Configuração padrão das páginas autenticadas."""

from __future__ import annotations

import traceback

import streamlit as st

from components.sidebar import render_sidebar
from core.auth import require_auth
from core.navigation import register_page_view
from core.styles import inject_global_css
from core.system_log import log_event


def set_page_config_once(**kwargs) -> None:
    """Evita erro de set_page_config duplicado entre app.py e pages/."""
    if st.session_state.get("_page_config_done"):
        return
    st.set_page_config(**kwargs)
    st.session_state["_page_config_done"] = True


def reset_page_config() -> None:
    """Permite reconfigurar título/sidebar ao trocar login → painel."""
    st.session_state.pop("_page_config_done", None)


def init_authenticated_page(title: str, icon: str, *, page_slug: str):
    """
    Deve ser a primeira chamada Streamlit da página.
    Sidebar expandida por padrão; recolhível pelo botão do Streamlit.
    """
    if not st.session_state.get("_page_config_done"):
        set_page_config_once(
            page_title=title,
            page_icon=icon,
            layout="wide",
            initial_sidebar_state="expanded",
        )
    inject_global_css()
    user = require_auth()
    from core.session_persistence import sync_auth_query_param

    sync_auth_query_param()
    register_page_view(page_slug)
    render_sidebar()
    return user


def safe_page_run(render_fn, page_name: str) -> None:
    """Executa render da página com log e exibição de erro."""
    try:
        render_fn()
    except Exception as exc:
        log_event("render", f"{page_name}: {exc}", exc)
        reset_page_config()
        set_page_config_once(page_title="Erro", page_icon="⚠️", layout="wide")
        inject_global_css()
        st.error(f"Erro ao carregar a página: {exc}")
        st.code(traceback.format_exc())
