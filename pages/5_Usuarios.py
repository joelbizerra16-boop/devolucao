"""Usuários — cadastro e listagem (administrador)."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.auth import get_current_user
from core.layout import init_authenticated_page, safe_page_run
from core.navigation import PAGE_USUARIOS
from core.constants import PERFIS_COMBO, perfil_para_label
from core.permissions import exigir_administrador
from core.styles import page_header
from services.usuario_service import (
    atualizar_usuario,
    buscar_usuario_por_id,
    cadastrar_usuario,
    excluir_usuario,
    listar_usuarios,
    usuario_e_protegido,
    usuario_pode_ser_editado,
)

SESSION_EDIT_KEY = "editando_usuario"
SESSION_EXCLUIR_KEY = "excluir_usuario_id"


def _limpar_formulario() -> None:
    for key in (SESSION_EDIT_KEY, SESSION_EXCLUIR_KEY):
        st.session_state.pop(key, None)


def _iniciar_edicao(usuario_id: int) -> None:
    if not usuario_pode_ser_editado(usuario_id):
        return
    st.session_state[SESSION_EDIT_KEY] = usuario_id
    st.session_state.pop(SESSION_EXCLUIR_KEY, None)


def _render_confirmacao_exclusao(usuario_logado_id: int) -> None:
    uid = st.session_state.get(SESSION_EXCLUIR_KEY)
    if not uid:
        return

    st.warning("Deseja realmente excluir este usuário?")
    c_ok, c_cancel = st.columns(2)
    with c_ok:
        if st.button("Sim, excluir", type="primary", key="usr_confirm_del", use_container_width=True):
            ok, msg = excluir_usuario(int(uid), usuario_logado_id)
            st.session_state.pop(SESSION_EXCLUIR_KEY, None)
            if int(uid) == st.session_state.get(SESSION_EDIT_KEY):
                _limpar_formulario()
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    with c_cancel:
        if st.button("Cancelar", key="usr_cancel_del", use_container_width=True):
            st.session_state.pop(SESSION_EXCLUIR_KEY, None)
            st.rerun()


def _render_lista_usuarios(usuario_logado_id: int) -> None:
    st.subheader("Usuários cadastrados")
    rows = listar_usuarios()
    if not rows:
        st.info("Nenhum usuário cadastrado.")
        return

    _render_confirmacao_exclusao(usuario_logado_id)

    widths = [2.2, 1.1, 1.2, 0.85, 1.35, 1.1]
    header = st.columns(widths)
    header[0].markdown("**Nome**")
    header[1].markdown("**Usuário**")
    header[2].markdown("**Perfil**")
    header[3].markdown("**Status**")
    header[4].markdown("**Data criação**")
    header[5].markdown("**Ações**")

    for r in rows:
        cols = st.columns(widths)
        cols[0].write(r.nome)
        cols[1].write(r.username)
        cols[2].write(perfil_para_label(r.perfil.value))
        cols[3].write("Ativo" if r.ativo else "Inativo")
        cols[4].write(
            r.created_at.strftime("%d/%m/%Y %H:%M") if r.created_at else "—"
        )
        protegido = usuario_e_protegido(r)
        btn_edit, btn_del = cols[5].columns(2)
        with btn_edit:
            if protegido:
                st.button(
                    "✏️",
                    key=f"usr_edit_{r.id}",
                    help="Usuário padrão do sistema — não editável",
                    disabled=True,
                    use_container_width=True,
                )
            elif st.button(
                "✏️", key=f"usr_edit_{r.id}", help="Editar", use_container_width=True
            ):
                _iniciar_edicao(r.id)
                st.rerun()
        with btn_del:
            if protegido:
                st.button(
                    "🗑️",
                    key=f"usr_del_{r.id}",
                    help="Usuário padrão do sistema — não excluível",
                    disabled=True,
                    use_container_width=True,
                )
            elif st.button(
                "🗑️", key=f"usr_del_{r.id}", help="Excluir", use_container_width=True
            ):
                st.session_state[SESSION_EXCLUIR_KEY] = r.id
                st.rerun()


def _render() -> None:
    init_authenticated_page("Usuários", "👥", page_slug=PAGE_USUARIOS)
    exigir_administrador()
    atual = get_current_user()
    if atual is None:
        st.stop()
    usuario_logado_id = atual.id

    page_header("Usuários", "Cadastro e controle de acesso ao sistema")

    editando_id = st.session_state.get(SESSION_EDIT_KEY)
    em_edicao = editando_id is not None

    col_form, col_lista = st.columns([0.5625, 1.2])

    with col_form:
        st.subheader("Cadastrar usuário")

        if em_edicao and st.button("Cancelar edição", use_container_width=True):
            _limpar_formulario()
            st.rerun()

        if em_edicao:
            user = buscar_usuario_por_id(int(editando_id))
            if user is None or usuario_e_protegido(user):
                _limpar_formulario()
                st.rerun()
            else:
                perfil_label = perfil_para_label(user.perfil.value)
                perfil_idx = (
                    PERFIS_COMBO.index(perfil_label)
                    if perfil_label in PERFIS_COMBO
                    else 0
                )
                with st.form("form_editar_usuario", clear_on_submit=False):
                    nome = st.text_input("NOME *", value=user.nome)
                    st.text_input("USUÁRIO *", value=user.username, disabled=True)
                    perfil = st.selectbox(
                        "PERFIL *",
                        options=PERFIS_COMBO,
                        index=perfil_idx,
                    )
                    senha = st.text_input(
                        "SENHA (opcional)",
                        type="password",
                        value="",
                        placeholder="Deixe vazio para manter",
                    )
                    salvar = st.form_submit_button(
                        "SALVAR ALTERAÇÕES",
                        type="primary",
                        use_container_width=True,
                    )

                if salvar:
                    ok, msg = atualizar_usuario(
                        int(editando_id), nome, perfil, senha
                    )
                    if ok:
                        st.success(msg)
                        _limpar_formulario()
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            with st.form("form_cadastro_usuario", clear_on_submit=True):
                nome = st.text_input("NOME *", placeholder="Nome completo")
                usuario = st.text_input("USUÁRIO *", placeholder="login.unico")
                perfil = st.selectbox("PERFIL *", options=PERFIS_COMBO, index=0)
                senha = st.text_input(
                    "SENHA *",
                    type="password",
                    placeholder="••••••••",
                )
                salvar = st.form_submit_button(
                    "CADASTRAR",
                    type="primary",
                    use_container_width=True,
                )

            if salvar:
                ok, msg = cadastrar_usuario(nome, usuario, perfil, senha)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with col_lista:
        _render_lista_usuarios(usuario_logado_id)


safe_page_run(_render, "Usuários")
