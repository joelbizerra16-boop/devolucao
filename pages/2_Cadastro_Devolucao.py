"""Cadastro Devolução — integrado à base SAP."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.layout import init_authenticated_page, safe_page_run
from core.navigation import PAGE_CADASTRO
from core.permissions import aviso_somente_leitura, pode_editar
from core.styles import page_header
from services.csv_repository import listar_motivos
from services.devolucao_service import buscar_dados_sap, cadastrar_devolucao


def _limpar_formulario_cadastro() -> None:
    """Remove chaves dos widgets antes de recriá-los (evita erro do Streamlit)."""
    for key in (
        "cad_nf",
        "cad_motivo",
        "cad_data_devolucao",
        "cad_sap_ok",
        "cad_sap_msg",
        "cad_sap_nf_validada",
    ):
        st.session_state.pop(key, None)


def _validar_nf_sap() -> None:
    """Valida NF na base SAP e grava status para exibir mensagem."""
    nf = str(st.session_state.get("cad_nf", "")).strip()
    if not nf:
        st.session_state.pop("cad_sap_ok", None)
        st.session_state.pop("cad_sap_msg", None)
        st.session_state.pop("cad_sap_nf_validada", None)
        return

    ok, msg, _ = buscar_dados_sap(nf)
    st.session_state["cad_sap_ok"] = ok
    st.session_state["cad_sap_nf_validada"] = nf
    if ok:
        st.session_state["cad_sap_msg"] = f"NF {nf} encontrada na base SAP."
    else:
        st.session_state["cad_sap_msg"] = msg or f"NF {nf} não encontrada na base SAP."


def _garantir_validacao_nf() -> None:
    """Revalida quando o valor da NF mudou (complementa on_change)."""
    nf = str(st.session_state.get("cad_nf", "")).strip()
    if not nf:
        st.session_state.pop("cad_sap_ok", None)
        st.session_state.pop("cad_sap_msg", None)
        st.session_state.pop("cad_sap_nf_validada", None)
        return
    if st.session_state.get("cad_sap_nf_validada") != nf:
        _validar_nf_sap()


def _exibir_feedback_nf() -> None:
    nf = str(st.session_state.get("cad_nf", "")).strip()
    if not nf or st.session_state.get("cad_sap_ok") is None:
        return
    msg = st.session_state.get("cad_sap_msg", "")
    if st.session_state.get("cad_sap_ok"):
        st.success(msg or f"NF {nf} encontrada na base SAP.")
    else:
        st.error(msg or f"NF {nf} não encontrada na base SAP.")


def _exibir_feedback_salvar() -> None:
    fb = st.session_state.pop("_cad_feedback", None)
    if not fb:
        return
    tipo, texto = fb
    if tipo == "success":
        st.success(texto)
    else:
        st.error(texto)


def _render() -> None:
    user = init_authenticated_page("Cadastro Devolução", "➕", page_slug=PAGE_CADASTRO)
    page_header("Cadastro Devolução", "Registre devoluções no relatório operacional")
    _exibir_feedback_salvar()
    aviso_somente_leitura()
    pode_salvar = pode_editar()

    motivos = listar_motivos()
    if not motivos:
        st.warning("Nenhum motivo cadastrado. Cadastre motivos em **Configuração Motivos**.")
        st.stop()

    if st.session_state.pop("_cad_limpar", False):
        _limpar_formulario_cadastro()

    responsavel = user.nome if user else ""

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("RESPONSÁVEL", value=responsavel, disabled=True)
    with col2:
        st.date_input(
            "D. DEVOLUÇÃO",
            value=date.today(),
            format="DD/MM/YYYY",
            key="cad_data_devolucao",
        )

    col3, col4 = st.columns(2)
    with col3:
        st.text_input(
            "NF *",
            placeholder="Digite o número da nota fiscal",
            key="cad_nf",
            on_change=_validar_nf_sap,
        )
        _garantir_validacao_nf()
        _exibir_feedback_nf()

    with col4:
        motivo = st.selectbox("MOTIVO *", options=motivos, key="cad_motivo")

    if st.button("SALVAR", type="primary", use_container_width=True, disabled=not pode_salvar):
        if not pode_salvar:
            st.warning("Usuário sem permissão.")
            st.stop()
        nf_nfd = str(st.session_state.get("cad_nf", "")).strip()
        if nf_nfd:
            _validar_nf_sap()

        ok, msg, _ = cadastrar_devolucao(
            data_devolucao=st.session_state.get("cad_data_devolucao", date.today()),
            nf_nfd=nf_nfd,
            motivo_devolucao=str(st.session_state.get("cad_motivo", "")),
            observacao="",
            usuario=responsavel,
        )
        if ok:
            st.session_state["_cad_feedback"] = ("success", msg)
            st.session_state["_cad_limpar"] = True
            st.rerun()
        else:
            st.session_state["_cad_feedback"] = ("error", msg)
            st.rerun()


safe_page_run(_render, "Cadastro Devolução")
