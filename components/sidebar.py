"""Sidebar — menu lateral fixo."""

from __future__ import annotations

import streamlit as st

from core.auth import get_current_user, logout
from core.constants import perfil_para_label
from core.permissions import is_administrador
from core.navigation import (
    PAGE_CADASTRO,
    PAGE_DASHBOARD,
    PAGE_MOTIVOS,
    PAGE_UPLOAD,
    PAGE_USUARIOS,
    page_link_query,
)
from core.utils import sidebar_logo_path


def _render_sidebar_logo() -> None:
    logo = sidebar_logo_path()
    if not logo:
        return
    _, col_logo, _ = st.columns([1, 1, 1])
    with col_logo:
        st.image(str(logo), width=95)


def render_sidebar() -> None:
    user = get_current_user()

    with st.sidebar:
        _render_sidebar_logo()

        st.markdown("---")
        st.page_link(
            "pages/6_Dashboard.py",
            label="Dashboard",
            icon="📊",
            query_params=page_link_query(PAGE_DASHBOARD),
        )
        # Consultar Devoluções — oculto temporariamente no menu
        st.page_link(
            "pages/2_Cadastro_Devolucao.py",
            label="Cadastro Devolução",
            icon="➕",
            query_params=page_link_query(PAGE_CADASTRO),
        )
        st.page_link(
            "pages/3_Upload_SAP.py",
            label="Upload Dados SAP",
            icon="📤",
            query_params=page_link_query(PAGE_UPLOAD),
        )
        st.page_link(
            "pages/4_Config_Motivos.py",
            label="Configuração Motivos",
            icon="⚙️",
            query_params=page_link_query(PAGE_MOTIVOS),
        )
        if is_administrador():
            st.page_link(
                "pages/5_Usuarios.py",
                label="Usuários",
                icon="👥",
                query_params=page_link_query(PAGE_USUARIOS),
            )

        st.markdown("---")
        if user:
            perfil_txt = perfil_para_label(user.perfil)
            st.caption(f"{user.nome} · @{user.username} · {perfil_txt}")
        if st.button("Sair", use_container_width=True, type="secondary"):
            logout()
            try:
                from pathlib import Path
                from streamlit.runtime.scriptrunner import get_script_run_ctx

                ctx = get_script_run_ctx()
                if ctx and Path(ctx.main_script_path).resolve().name == "app.py":
                    st.rerun()
                else:
                    st.switch_page("app.py")
            except Exception:
                st.switch_page("app.py")
