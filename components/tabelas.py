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


# Cor do heat map — mesma base de COR_DEVOLUCOES (dashboard_service)
_HEATMAP_RGB = "47, 128, 237"


def _config_coluna_percentual():
    """
    Coluna de percentual compatível com a versão instalada do Streamlit.

    - ProgressBarColumn: versões mais recentes
    - ProgressColumn: streamlit>=1.33 (ex.: 1.53)
    - None: fallback via Pandas Styler
    """
    cc = st.column_config
    kwargs = {
        "label": "Percentual",
        "format": "%.1f%%",
        "min_value": 0,
        "max_value": 100,
    }
    if hasattr(cc, "ProgressBarColumn"):
        return cc.ProgressBarColumn(**kwargs)
    if hasattr(cc, "ProgressColumn"):
        return cc.ProgressColumn(**kwargs)
    return None


def _heatmap_percentual_styler(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    """Heat map na coluna Percentual — fallback quando não há ProgressColumn."""
    col = "Percentual"

    def _estilo_celula(val: object) -> str:
        try:
            pct = float(val)
        except (TypeError, ValueError):
            return ""
        intensidade = max(0.0, min(100.0, pct)) / 100.0
        alpha = 0.15 + intensidade * 0.55
        return f"background-color: rgba({_HEATMAP_RGB}, {alpha:.2f}); color: #e6edf3;"

    styler = df.style
    if hasattr(styler, "map"):
        styler = styler.map(_estilo_celula, subset=[col])
    else:
        styler = styler.applymap(_estilo_celula, subset=[col])
    return styler.format({col: "{:.1f}%"})


def _render_dataframe_resumo(
    df: pd.DataFrame,
    column_config: dict,
    *,
    height: int,
) -> None:
    pct_cfg = _config_coluna_percentual()
    if pct_cfg is not None:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=height,
            column_config={**column_config, "Percentual": pct_cfg},
        )
        return

    st.dataframe(
        _heatmap_percentual_styler(df),
        use_container_width=True,
        hide_index=True,
        height=height,
    )


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


def _altura_tabela_resumo(qtd_linhas: int) -> int:
    if qtd_linhas <= 0:
        return 140
    return min(56 + qtd_linhas * 40, 640)


def render_tabela_resumo_motivos(df: pd.DataFrame, height: int | None = None) -> None:
    """Tabela analítica agregada por motivo — Resumo Operacional."""
    if df.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
        return

    altura = height if height is not None else _altura_tabela_resumo(len(df))
    _render_dataframe_resumo(
        df,
        {
            "Motivo": st.column_config.TextColumn("Motivo", width="large"),
            "Quantidade": st.column_config.NumberColumn("Quantidade", format="%d"),
            "Valor Total": st.column_config.TextColumn("Valor Total", width="medium"),
        },
        height=altura,
    )


def render_tabela_resumo_clientes(df: pd.DataFrame, height: int | None = None) -> None:
    """Tabela analítica agregada por cliente — Resumo Operacional."""
    if df.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
        return

    altura = height if height is not None else _altura_tabela_resumo(len(df))
    _render_dataframe_resumo(
        df,
        {
            "Código": st.column_config.TextColumn("Código", width="small"),
            "Cliente": st.column_config.TextColumn("Cliente", width="large"),
            "Quantidade": st.column_config.NumberColumn("Quantidade", format="%d"),
            "Valor Total": st.column_config.TextColumn("Valor Total", width="medium"),
        },
        height=altura,
    )


def render_tabela_resumo_analitica(
    df: pd.DataFrame,
    *,
    modo: str,
    height: int | None = None,
) -> None:
    """Tabela analítica dinâmica — Motivos ou Clientes (Resumo Operacional)."""
    if modo == "Clientes":
        render_tabela_resumo_clientes(df, height=height)
    else:
        render_tabela_resumo_motivos(df, height=height)


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
