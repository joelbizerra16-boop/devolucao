"""Resumo Operacional de Devoluções — indicadores, gráficos e tabela analítica."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.cards import render_resumo_cards
from components.chart_card import render_plotly_in_card
from components.tabelas import render_tabela_resumo_analitica
from core.cache_read import limpar_cache_leitura
from core.layout import init_authenticated_page, safe_page_run
from core.navigation import PAGE_RESUMO
from core.styles import page_header
from core.tratativa_constants import TRATATIVA_FILTRO_TODOS, TRATATIVA_FILTROS_UI
from services.resumo_operacional_service import (
    FILTRO_TODOS_CLIENTE,
    FILTRO_TODOS_MOTIVO,
    MESES_LABEL,
    MODOS_TABELA,
    ORDENAR_QUANTIDADE,
    ORDENAR_VALOR,
    MODOS_ORDENACAO,
    carregar_resumo_cache,
    carregar_tabela_resumo_cache,
    export_tabela_resumo_excel_bytes,
    mes_label_para_numero,
    nome_arquivo_resumo_operacional,
    obter_anos_disponiveis,
    obter_graficos_resumo,
    obter_opcoes_filtros_cache,
    obter_periodo_padrao,
)


def _render() -> None:
    from core.perf_monitor import track_page

    with track_page("resumo"):
        _render_resumo()


def _selectbox_cliente(
    opcoes_cliente: tuple[tuple[str, str], ...],
    *,
    mes: int,
    ano: int,
) -> str:
    rotulos = [FILTRO_TODOS_CLIENTE] + [item[1] for item in opcoes_cliente]
    codigos = [FILTRO_TODOS_CLIENTE] + [item[0] for item in opcoes_cliente]
    idx = st.selectbox(
        "CLIENTE",
        options=range(len(rotulos)),
        format_func=lambda i: rotulos[i],
        key=f"resumo_filtro_cliente_{mes}_{ano}",
    )
    return codigos[idx]


def _render_resumo() -> None:
    init_authenticated_page("Resumo", "📈", page_slug=PAGE_RESUMO)

    page_header(
        "Resumo",
        "Indicadores operacionais e análise agregada de devoluções",
    )

    mes_padrao, ano_padrao = obter_periodo_padrao()
    anos = obter_anos_disponiveis() or [ano_padrao]
    if ano_padrao not in anos:
        anos = sorted(set(anos + [ano_padrao]), reverse=True)

    fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([1.1, 0.8, 1.6, 1.4, 1.1, 0.7])
    with fc1:
        mes_label = st.selectbox(
            "MÊS",
            options=MESES_LABEL,
            index=max(0, min(mes_padrao - 1, 11)),
            key="resumo_filtro_mes",
        )
    with fc2:
        ano_idx = anos.index(ano_padrao) if ano_padrao in anos else 0
        ano_sel = st.selectbox(
            "ANO",
            options=anos,
            index=ano_idx,
            key="resumo_filtro_ano",
        )

    mes_num = mes_label_para_numero(mes_label)
    ano = int(ano_sel)
    opcoes = obter_opcoes_filtros_cache(mes_num, ano)

    with fc3:
        cliente_sel = _selectbox_cliente(opcoes["clientes"], mes=mes_num, ano=ano)
    with fc4:
        motivos = [FILTRO_TODOS_MOTIVO, *list(opcoes["motivos"])]
        motivo_sel = st.selectbox(
            "MOTIVO",
            options=motivos,
            key=f"resumo_filtro_motivo_{mes_num}_{ano}",
        )
    with fc5:
        tratativa_sel = st.selectbox(
            "TRATATIVA",
            options=TRATATIVA_FILTROS_UI,
            index=0,
            key="resumo_filtro_tratativa",
        )
    with fc6:
        st.write("")
        if st.button("Atualizar", type="primary", use_container_width=True):
            limpar_cache_leitura()
            st.rerun()

    cliente = cliente_sel or FILTRO_TODOS_CLIENTE
    motivo = motivo_sel or FILTRO_TODOS_MOTIVO
    tratativa = tratativa_sel or TRATATIVA_FILTRO_TODOS

    dados = carregar_resumo_cache(mes_num, ano, cliente, motivo, tratativa)
    graficos = obter_graficos_resumo(mes_num, ano, cliente, motivo, tratativa)

    render_resumo_cards(dados["cards"])

    gc1, gc2 = st.columns(2)
    with gc1:
        render_plotly_in_card(graficos["motivos_qtd"], "resumo_chart_motivos_qtd")
    with gc2:
        render_plotly_in_card(graficos["motivos_valor"], "resumo_chart_motivos_valor")

    gc3, gc4 = st.columns(2)
    with gc3:
        render_plotly_in_card(graficos["clientes_qtd"], "resumo_chart_clientes_qtd")
    with gc4:
        render_plotly_in_card(graficos["clientes_valor"], "resumo_chart_clientes_valor")

    st.markdown("---")
    st.subheader("Tabela analítica")

    tb_analisar, tb_espaco, tb_classificar, tb_export = st.columns([2.4, 1.15, 2.5, 1.35])
    with tb_analisar:
        modo_tabela = st.radio(
            "Analisar por",
            options=MODOS_TABELA,
            horizontal=True,
            key="resumo_modo_tabela",
            label_visibility="collapsed",
        )
    with tb_classificar:
        ordenacao_tabela = st.radio(
            "Classificar por",
            options=MODOS_ORDENACAO,
            horizontal=True,
            key="resumo_ordenacao_tabela",
            label_visibility="collapsed",
        )

    df_tabela = carregar_tabela_resumo_cache(
        mes_num,
        ano,
        cliente,
        motivo,
        tratativa,
        modo_tabela,
        ordenacao_tabela,
    )

    with tb_export:
        st.write("")
        st.download_button(
            "Exportar Excel",
            data=export_tabela_resumo_excel_bytes(df_tabela, modo_tabela),
            file_name=nome_arquivo_resumo_operacional(),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="secondary",
            key="resumo_export_xlsx",
        )

    render_tabela_resumo_analitica(df_tabela, modo=modo_tabela)


safe_page_run(_render, "Resumo")
