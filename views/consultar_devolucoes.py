"""Conteúdo da página Consultar Devoluções."""

from __future__ import annotations

import streamlit as st

from components.cards import render_operational_cards
from components.tabelas import render_tabela_relatorio
from core.cache_read import limpar_cache_leitura
from core.layout import init_authenticated_page
from core.navigation import PAGE_CONSULTAR
from core.styles import page_header
from services.devolucao_service import listar_devolucoes, obter_metricas_cards


def render() -> None:
    init_authenticated_page("Consultar Devoluções", "🔍", page_slug=PAGE_CONSULTAR)

    page_header("Consultar Devoluções", "Pesquise e filtre as devoluções cadastradas")

    fc1, fc2, fc3 = st.columns([2, 1, 1])
    with fc1:
        busca = st.text_input(
            "Busca",
            placeholder="NF, responsável, cidade, vendedor, motivo...",
        )
    with fc2:
        st.selectbox("Status", ["Todos"])
    with fc3:
        st.write("")
        if st.button("Atualizar", type="primary", use_container_width=True):
            limpar_cache_leitura()
            st.rerun()

    metricas = obter_metricas_cards()
    render_operational_cards(metricas)

    st.markdown("---")
    df = listar_devolucoes(busca=busca)
    render_tabela_relatorio(df)
