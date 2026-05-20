"""Tabelas operacionais."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.utils import devolucoes_to_display_df

COLUNAS_DASHBOARD = [
    "DATA + USUARIO",
    "MOTIVO",
    "NF",
    "VALOR",
    "COD CLIENTE",
    "VENDEDOR",
]

COLUNAS_LISTVIEW = [
    "RESPONSAVEL / DEVOLUÇÃO",
    "D. EMISSÃO",
    "NF/NFD",
    "COD CLIENTE",
    "VENDEDOR",
    "VALOR",
    "CIDADE",
    "BAIRRO",
    "MOTIVO DEVOLUÇÃO",
]


def _altura_auto_linhas(qtd_linhas: int) -> int:
    """Altura dinâmica — linhas com responsável + data em duas linhas."""
    if qtd_linhas <= 0:
        return 140
    return min(56 + qtd_linhas * 48, 720)


def render_tabela_relatorio(df: pd.DataFrame, height: int | None = None) -> None:
    """Tabela principal — relatório operacional (list view corporativa)."""
    if df.empty:
        st.info("Nenhuma devolução encontrada para os filtros selecionados.")
        return

    colunas = [c for c in COLUNAS_LISTVIEW if c in df.columns]
    if not colunas:
        colunas = list(df.columns)

    altura = height if height is not None else _altura_auto_linhas(len(df))

    st.dataframe(
        df[colunas],
        use_container_width=True,
        hide_index=True,
        height=altura,
        column_config={
            "RESPONSAVEL / DEVOLUÇÃO": st.column_config.TextColumn(
                "RESPONSAVEL / DEVOLUÇÃO",
                width="medium",
                help="Responsável e data da devolução",
            ),
            "D. EMISSÃO": st.column_config.TextColumn("D. EMISSÃO", width="small"),
            "NF/NFD": st.column_config.TextColumn("NF/NFD", width="small"),
            "COD CLIENTE": st.column_config.TextColumn("COD CLIENTE", width="small"),
            "VENDEDOR": st.column_config.TextColumn("VENDEDOR", width="medium"),
            "VALOR": st.column_config.TextColumn("VALOR", width="small"),
            "CIDADE": st.column_config.TextColumn("CIDADE", width="medium"),
            "BAIRRO": st.column_config.TextColumn("BAIRRO", width="medium"),
            "MOTIVO DEVOLUÇÃO": st.column_config.TextColumn(
                "MOTIVO DEVOLUÇÃO",
                width="large",
            ),
        },
    )


def render_tabela_dashboard(df: pd.DataFrame, height: int | None = None) -> None:
    """Listview executiva do dashboard."""
    if df.empty:
        st.info("Nenhuma devolução encontrada para o período selecionado.")
        return

    altura = height if height is not None else _altura_auto_linhas(len(df))
    st.dataframe(
        df[COLUNAS_DASHBOARD],
        use_container_width=True,
        hide_index=True,
        height=altura,
        column_config={
            "DATA + USUARIO": st.column_config.TextColumn(
                "DATA + USUARIO",
                width="medium",
                help="Data da devolução e responsável",
            ),
            "MOTIVO": st.column_config.TextColumn("MOTIVO", width="large"),
            "NF": st.column_config.TextColumn("NF", width="small"),
            "VALOR": st.column_config.TextColumn("VALOR", width="small"),
            "COD CLIENTE": st.column_config.TextColumn("COD CLIENTE", width="small"),
            "VENDEDOR": st.column_config.TextColumn("VENDEDOR", width="medium"),
        },
    )


def render_tabela_operacional(df: pd.DataFrame, height: int = 420) -> None:
    if df.empty:
        st.info("Nenhuma devolução encontrada para os filtros selecionados.")
        return

    display = devolucoes_to_display_df(df)
    colunas = ["numero", "pedido", "cliente", "nf_numero", "status", "prioridade", "data_abertura"]
    colunas = [c for c in colunas if c in display.columns]

    st.dataframe(
        display[colunas],
        use_container_width=True,
        hide_index=True,
        height=height,
        column_config={
            "numero": st.column_config.TextColumn("Nº Devolução", width="medium"),
            "pedido": st.column_config.TextColumn("Pedido", width="small"),
            "cliente": st.column_config.TextColumn("Cliente", width="large"),
            "nf_numero": st.column_config.TextColumn("NF", width="small"),
            "status": st.column_config.TextColumn("Status", width="medium"),
            "prioridade": st.column_config.TextColumn("Prioridade", width="small"),
            "data_abertura": st.column_config.TextColumn("Abertura", width="medium"),
        },
    )
