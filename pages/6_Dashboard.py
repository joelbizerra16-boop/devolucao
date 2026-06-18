"""Dashboard operacional — indicadores, gráficos e listview."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.cards import render_dashboard_cards
from components.chart_card import render_plotly_in_card
from components.listagem_dashboard import render_listagem_operacional
from core.auth import get_current_user
from core.layout import init_authenticated_page, safe_page_run
from core.navigation import PAGE_DASHBOARD
from core.styles import inject_dashboard_export_toolbar_css, page_header
from services.export_dashboard_service import nome_arquivo_exportacao
from core.constants import TRATATIVA_FILTRO_TODOS, TRATATIVA_FILTROS_UI
from core.cache_read import limpar_cache_leitura
from core.tratativa_utils import filtrar_linhas_por_tratativa
from services.dashboard_service import (
    MESES_LABEL,
    carregar_dashboard,
    export_excel_dashboard_cache,
    export_pdf_dashboard_cache,
    listar_devolucoes_periodo_cache,
    mes_label_para_numero,
    listar_devolucoes_periodo_dashboard,
    obter_anos_disponiveis,
    obter_graficos,
    obter_periodo_padrao,
)


def _render() -> None:
    from core.perf_monitor import track_page

    with track_page("dashboard"):
        _render_dashboard()


def _render_dashboard() -> None:
    init_authenticated_page("Dashboard", "📊", page_slug=PAGE_DASHBOARD)

    page_header(
        "Dashboard",
        "Indicadores operacionais e análise de devoluções",
    )

    mes_padrao, ano_padrao = obter_periodo_padrao()
    anos = obter_anos_disponiveis() or [ano_padrao]
    if ano_padrao not in anos:
        anos = sorted(set(anos + [ano_padrao]), reverse=True)

    fc1, fc2, fc3 = st.columns([2, 1, 1])
    with fc1:
        mes_label = st.selectbox(
            "MÊS",
            options=MESES_LABEL,
            index=max(0, min(mes_padrao - 1, 11)),
            key="dash_filtro_mes",
        )
    with fc2:
        ano_idx = anos.index(ano_padrao) if ano_padrao in anos else 0
        ano_sel = st.selectbox(
            "ANO",
            options=anos,
            index=ano_idx,
            key="dash_filtro_ano",
        )
    with fc3:
        st.write("")
        if st.button("Atualizar", type="primary", use_container_width=True):
            limpar_cache_leitura()
            st.rerun()

    mes_num = mes_label_para_numero(mes_label)
    ano = int(ano_sel)

    dados = carregar_dashboard(mes_num, ano)
    graficos = obter_graficos(mes_num, ano)

    # | Impacto Financeiro | Total de Devoluções | Principal Motivo |
    render_dashboard_cards(dados["cards"])

    # | Total de Devolução (Dia) — largura total |
    render_plotly_in_card(graficos["devolucoes_dia"], "dash_chart_devolucoes_dia")

    # | Impacto Financeiro (Mês) | Total de Devolução (Mês) |
    gc1, gc2 = st.columns(2)
    with gc1:
        render_plotly_in_card(graficos["impacto_mes"], "dash_chart_impacto_mes")
    with gc2:
        render_plotly_in_card(graficos["devolucoes_mes"], "dash_chart_devolucoes_mes")

    st.markdown("---")
    st.subheader("Listagem operacional")

    idx_mes_lista = (
        MESES_LABEL.index(mes_label) if mes_label in MESES_LABEL else mes_padrao - 1
    )
    idx_ano_lista = anos.index(ano) if ano in anos else 0

    inject_dashboard_export_toolbar_css()

    # BUSCA + TRATATIVA; ícones PDF + Excel à direita
    lf1, lf2, lf3, lf4, lf5, lf6 = st.columns([1.1, 0.9, 1.4, 1.1, 0.38, 0.38])
    with lf1:
        lista_mes_label = st.selectbox(
            "MÊS",
            options=MESES_LABEL,
            index=idx_mes_lista,
            key="dash_lista_mes",
        )
    with lf2:
        lista_ano = st.selectbox(
            "ANO",
            options=anos,
            index=idx_ano_lista,
            key="dash_lista_ano",
        )
    with lf3:
        busca_lista = st.text_input(
            "BUSCA",
            placeholder="NF, usuário, motivo, vendedor, código cliente...",
            key="dash_lista_busca",
        )
    with lf4:
        tratativa_filtro = st.selectbox(
            "TRATATIVA",
            options=TRATATIVA_FILTROS_UI,
            index=0,
            key="dash_lista_tratativa",
        )

    lista_mes_num = mes_label_para_numero(lista_mes_label)
    lista_ano_num = int(lista_ano)
    busca_txt = busca_lista or ""
    filtro_tratativa = tratativa_filtro or TRATATIVA_FILTRO_TODOS
    rows_cache = listar_devolucoes_periodo_cache(
        lista_mes_num,
        lista_ano_num,
        busca_txt,
    )
    rows_lista = listar_devolucoes_periodo_dashboard(
        lista_mes_num,
        lista_ano_num,
        busca=busca_txt,
        tratativa_filtro=filtro_tratativa,
    )
    user = get_current_user()
    usuario_exp = user.nome if user else "Sistema"
    rows_export = tuple(filtrar_linhas_por_tratativa(list(rows_cache), filtro_tratativa))
    pdf_bytes = export_pdf_dashboard_cache(
        lista_mes_label,
        lista_ano_num,
        busca_txt,
        usuario_exp,
        rows_export,
    )
    xlsx_bytes = export_excel_dashboard_cache(rows_export)

    with lf5:
        st.markdown('<span class="dash-export-marker-pdf"></span>', unsafe_allow_html=True)
        st.download_button(
            label="",
            data=pdf_bytes,
            file_name=nome_arquivo_exportacao("pdf", lista_mes_label, lista_ano_num),
            mime="application/pdf",
            icon=":material/picture_as_pdf:",
            help="Exportar PDF",
            use_container_width=True,
            key="dash_export_pdf",
        )
    with lf6:
        st.markdown('<span class="dash-export-marker-xlsx"></span>', unsafe_allow_html=True)
        st.download_button(
            label="",
            data=xlsx_bytes,
            file_name=nome_arquivo_exportacao("xlsx", lista_mes_label, lista_ano_num),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            icon=":material/table_chart:",
            help="Exportar Excel",
            use_container_width=True,
            key="dash_export_xlsx",
        )

    filtro_sig = (lista_mes_num, lista_ano_num, busca_txt, filtro_tratativa)
    if st.session_state.get("dash_lista_filtro_sig") != filtro_sig:
        st.session_state["dash_lista_filtro_sig"] = filtro_sig
        st.session_state["dash_lista_page"] = 1

    render_listagem_operacional(rows_lista)


safe_page_run(_render, "Dashboard")
