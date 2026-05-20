"""
Sistema de Devolução — ponto de entrada.
Login corporativo + painel operacional.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.auth import init_session_state, is_authenticated, login
from core.navigation import PAGE_DASHBOARD, route_authenticated_entry, set_current_page
from core.layout import reset_page_config, set_page_config_once
from core.styles import inject_global_css, inject_login_css
from core.system_log import log_event
from core.utils import asset_path, sidebar_logo_path
from core.db import check_connection, init_db
from services.csv_repository import init_csv_storage
from services.usuario_service import seed_default_users


def _bootstrap() -> None:
    ok, msg = check_connection()
    if not ok:
        raise ConnectionError(msg)
    init_db()
    init_csv_storage()
    seed_default_users()


def _render_login() -> None:
    """Login — logo e formulário lado a lado, alinhados ao centro."""
    bg = asset_path("background.png")
    logo = sidebar_logo_path()
    bg_url = f"file:///{bg.as_posix()}" if bg else None

    inject_login_css(bg_url)

    col_brand, col_form = st.columns([1, 1], gap="small")

    with col_brand:
        st.markdown(
            '<span class="login-shell-marker login-brand-col"></span>',
            unsafe_allow_html=True,
        )
        if logo:
            st.image(str(logo), width=300)

    with col_form:
        st.markdown(
            '<span class="login-shell-marker login-form-col"></span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="login-form-card">
                <p class="login-title">Acesso ao sistema</p>
                <p class="login-subtitle login-module-name">DEVOLUÇÕES</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Usuário", placeholder="seu.usuario")
            password = st.text_input("Senha", type="password", placeholder="••••••••")
            submitted = st.form_submit_button(
                "Entrar", type="primary", use_container_width=True
            )

        if submitted:
            ok, msg = login(username, password)
            if ok:
                reset_page_config()
                set_current_page(PAGE_DASHBOARD)
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


def _render_authenticated_home() -> None:
    """Restaura a última página visitada ou abre o dashboard após login."""
    route_authenticated_entry()


def main() -> None:
    init_session_state()
    autenticado = is_authenticated()

    set_page_config_once(
        page_title="Devolução WMS",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded" if autenticado else "collapsed",
    )

    try:
        _bootstrap()

        if autenticado:
            inject_global_css()
            _render_authenticated_home()
        else:
            _render_login()

    except ConnectionError as exc:
        log_event("db", str(exc), exc)
        st.error(
            "Não foi possível conectar ao banco de dados. "
            "Configure **DATABASE_URL** (PostgreSQL Supabase) no `.env` ou nos secrets do Streamlit Cloud."
        )
        st.caption(str(exc))
    except Exception as exc:
        log_event("app", str(exc), exc)
        st.error(f"Erro ao iniciar o sistema: {exc}")
        st.code(traceback.format_exc())


main()
