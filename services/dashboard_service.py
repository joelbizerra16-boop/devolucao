"""Serviço do dashboard operacional — cards, gráficos e listview."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.cache_read import TTL_DASHBOARD
from core.tratativa_constants import TRATATIVA_FILTRO_TODOS
from core.orm_serialize import parse_iso_datetime
from core.tratativa_utils import (
    calcular_indicadores_tratativa,
    filtrar_linhas_por_tratativa,
    formatar_pct_analisada,
)
from core.styles import COLORS
from core.theme import (
    PLOTLY_AXIS_SIZE,
    PLOTLY_BAR_LABEL_SIZE,
    PLOTLY_FONT,
    PLOTLY_HOVER_SIZE,
    PLOTLY_TITLE_SIZE,
)
from repositories import dashboard_repository
from services.devolucao_service import (
    _formatar_data,
    _formatar_valor_br,
    _nome_responsavel_exibicao,
    _texto_celula,
)

MESES_LABEL = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]

MESES_NUM = list(range(1, 13))

CHART_HEIGHT = 250
CHART_HEIGHT_DIA = 220
CHART_BG = "rgba(17,24,39,0.95)"
CHART_GRID = "rgba(255,255,255,0.04)"

COR_DEVOLUCOES = "#2F80ED"
COR_DEVOLUCOES_MUTED = "rgba(47, 128, 237, 0.38)"
COR_FINANCEIRO = "#D4A021"
COR_FINANCEIRO_MUTED = "rgba(212, 160, 33, 0.38)"


def mes_label_para_numero(label: str) -> int:
    try:
        return MESES_LABEL.index(label.strip()) + 1
    except ValueError:
        return 1


def mes_numero_para_label(num: int) -> str:
    if 1 <= num <= 12:
        return MESES_LABEL[num - 1]
    return MESES_LABEL[0]


def obter_anos_disponiveis() -> list[int]:
    return obter_anos_disponiveis_cache()


@st.cache_data(ttl=TTL_DASHBOARD, show_spinner=False)
def obter_anos_disponiveis_cache() -> list[int]:
    anos = dashboard_repository.listar_anos_disponiveis()
    if anos:
        return anos
    from datetime import datetime

    return [datetime.now().year]


def obter_periodo_padrao() -> tuple[int, int]:
    return obter_periodo_padrao_cache()


@st.cache_data(ttl=TTL_DASHBOARD, show_spinner=False)
def obter_periodo_padrao_cache() -> tuple[int, int]:
    return dashboard_repository.obter_periodo_padrao()


def _serializar_devolucao_row(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)
    data_dev = row.data_devolucao
    if hasattr(data_dev, "isoformat"):
        data_dev = data_dev.isoformat()
    return {
        "id": int(row.id),
        "data_devolucao": str(data_dev),
        "usuario": row.usuario,
        "usuario_ultima_edicao": row.usuario_ultima_edicao,
        "motivo_devolucao": row.motivo_devolucao,
        "nf_nfd": row.nf_nfd,
        "valor_nf": row.valor_nf,
        "cod_cliente": row.cod_cliente,
        "vendedor": row.vendedor,
    }


def _deserializar_devolucao_row(dados: dict[str, Any]) -> SimpleNamespace:
    texto_data = dados.get("data_devolucao")
    try:
        data_dev = date.fromisoformat(str(texto_data))
    except (TypeError, ValueError):
        data_dev = None
    return SimpleNamespace(
        id=dados.get("id"),
        data_devolucao=data_dev,
        usuario=dados.get("usuario"),
        usuario_ultima_edicao=dados.get("usuario_ultima_edicao"),
        motivo_devolucao=dados.get("motivo_devolucao"),
        tratativa=dados.get("tratativa") or "Aguardando",
        tratativa_atualizada_em=parse_iso_datetime(dados.get("tratativa_atualizada_em")),
        tratativa_atualizada_por=dados.get("tratativa_atualizada_por"),
        nf_nfd=dados.get("nf_nfd"),
        valor_nf=dados.get("valor_nf"),
        cod_cliente=dados.get("cod_cliente"),
        vendedor=dados.get("vendedor"),
    )


def _aplicar_filtro_tratativa_rows(
    rows: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    tratativa_filtro: str,
) -> list[dict[str, Any]]:
    filtro = (tratativa_filtro or TRATATIVA_FILTRO_TODOS).strip()
    return filtrar_linhas_por_tratativa(list(rows), filtro)


@st.cache_data(ttl=TTL_DASHBOARD, show_spinner=False)
def listar_devolucoes_periodo_cache(
    mes: int,
    ano: int,
    busca: str = "",
) -> tuple[dict[str, Any], ...]:
    from core.search_utils import normalizar_texto_busca

    busca_norm = normalizar_texto_busca(busca or "")
    rows = dashboard_repository.listar_periodo(mes, ano, busca=busca_norm)
    return tuple(rows)


def listar_devolucoes_periodo_dashboard(
    mes: int,
    ano: int,
    busca: str = "",
    tratativa_filtro: str = TRATATIVA_FILTRO_TODOS,
) -> list[SimpleNamespace]:
    """Linhas da listagem operacional (cache + objetos leves para a UI)."""
    rows = _aplicar_filtro_tratativa_rows(
        listar_devolucoes_periodo_cache(mes, ano, busca),
        tratativa_filtro,
    )
    return [_deserializar_devolucao_row(d) for d in rows]


def obter_indicadores_tratativa_dashboard(
    mes: int,
    ano: int,
    busca: str = "",
    tratativa_filtro: str = TRATATIVA_FILTRO_TODOS,
) -> dict[str, str]:
    """Indicadores de tratativa a partir do mesmo conjunto filtrado da listagem."""
    rows = _aplicar_filtro_tratativa_rows(
        listar_devolucoes_periodo_cache(mes, ano, busca),
        tratativa_filtro,
    )
    raw = calcular_indicadores_tratativa(rows)
    return {chave: str(valor) for chave, valor in raw.items()}


def _rotulo_qtd_devolucoes(qtd: int) -> str:
    n = int(qtd or 0)
    return f"{n} devolução" if n == 1 else f"{n} devoluções"


def _cards_formatados(raw: dict[str, Any]) -> dict[str, str]:
    motivo = raw.get("principal_motivo")
    motivo_qtd = int(raw.get("principal_motivo_qtd") or 0)
    if motivo:
        principal = motivo
        principal_sub = _rotulo_qtd_devolucoes(motivo_qtd)
    else:
        principal = "N/A"
        principal_sub = ""

    pct_txt = formatar_pct_analisada(float(raw.get("pct_analisada") or 0))

    return {
        "impacto_financeiro": _formatar_valor_br(raw.get("soma_valor_nf", 0)),
        "devolucoes": str(int(raw.get("total_devolucoes") or 0)),
        "aguardando": str(int(raw.get("total_aguardando") or 0)),
        "pct_analisada": pct_txt,
        "principal_motivo": principal,
        "principal_motivo_sub": principal_sub,
    }


def preparar_listview_dashboard(rows: list) -> pd.DataFrame:
    colunas = [
        "DATA + USUARIO",
        "MOTIVO",
        "NF",
        "VALOR",
        "COD CLIENTE",
        "VENDEDOR",
    ]
    if not rows:
        return pd.DataFrame(columns=colunas)

    linhas = []
    for r in rows:
        data_txt = _formatar_data(r.data_devolucao)
        usuario = _nome_responsavel_exibicao(r)
        linhas.append(
            {
                "DATA + USUARIO": f"{data_txt}\n{usuario}",
                "MOTIVO": _texto_celula(r.motivo_devolucao),
                "NF": _texto_celula(r.nf_nfd),
                "VALOR": _formatar_valor_br(r.valor_nf),
                "COD CLIENTE": _texto_celula(r.cod_cliente),
                "VENDEDOR": _texto_celula(r.vendedor),
            }
        )
    return pd.DataFrame(linhas, columns=colunas)


def _rotulo_int(valor: float | int) -> str:
    return str(int(valor))


def _rotulo_moeda(valor: float, *, decimais: bool = True) -> str:
    num = float(valor)
    if decimais:
        texto = f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        texto = f"{int(round(num)):,}".replace(",", ".")
    return f"R$ {texto}"


def _layout_plotly(titulo: str, height: int | None = None) -> dict[str, Any]:
    return dict(
        title=dict(
            text=titulo,
            font=dict(size=PLOTLY_TITLE_SIZE, family=PLOTLY_FONT, color="#ffffff"),
            x=0,
            xanchor="left",
            pad=dict(t=6, b=10),
        ),
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(color=COLORS["text"], family=PLOTLY_FONT, size=PLOTLY_AXIS_SIZE),
        height=height if height is not None else CHART_HEIGHT,
        margin=dict(l=18, r=18, t=52, b=18),
        xaxis=dict(
            gridcolor=CHART_GRID,
            linecolor="rgba(255,255,255,0.05)",
            tickfont=dict(color=COLORS["text_muted"], size=PLOTLY_AXIS_SIZE, family=PLOTLY_FONT),
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            visible=False,
            showticklabels=False,
            showgrid=True,
            gridcolor=CHART_GRID,
            zeroline=False,
            showline=False,
        ),
        bargap=0.32,
        hovermode="closest",
        hoverlabel=dict(
            bgcolor="#111827",
            font_size=PLOTLY_HOVER_SIZE,
            font_color="white",
            bordercolor="rgba(255,255,255,0.12)",
            font_family=PLOTLY_FONT,
        ),
        uniformtext_minsize=9,
        uniformtext_mode="show",
    )


def _ocultar_eixo_y(fig: go.Figure) -> None:
    fig.update_yaxes(
        visible=False,
        showticklabels=False,
        showgrid=True,
        gridcolor=CHART_GRID,
        zeroline=False,
        showline=False,
    )


def _barra(
    x: list,
    y: list,
    text: list[str],
    colors: str | list[str],
    hovertemplate: str,
) -> go.Bar:
    return go.Bar(
        x=x,
        y=y,
        text=text,
        textposition="outside",
        textfont=dict(color="#e6edf3", size=PLOTLY_BAR_LABEL_SIZE, family=PLOTLY_FONT),
        marker=dict(
            color=colors,
            line=dict(width=0),
            cornerradius=8,
        ),
        width=0.52,
        hovertemplate=hovertemplate,
        cliponaxis=False,
    )


def _finalizar_figura(
    fig: go.Figure, titulo: str, height: int | None = None
) -> go.Figure:
    fig.update_layout(**_layout_plotly(titulo, height=height))
    _ocultar_eixo_y(fig)
    return fig


def grafico_devolucoes_por_dia(
    mes: int,
    ano: int,
    rows: list[tuple[date, int]] | None = None,
) -> go.Figure:
    if rows is None:
        rows = dashboard_repository.devolucoes_por_dia(mes, ano)
    if rows:
        labels = [d.strftime("%d/%m") for d, _ in rows]
        valores = [v for _, v in rows]
    else:
        labels, valores = [], []

    rotulos = [_rotulo_int(v) for v in valores]
    fig = go.Figure(
        data=[
            _barra(
                labels,
                valores,
                rotulos,
                COR_DEVOLUCOES,
                "%{x}<br><b>%{y}</b> devoluções<extra></extra>",
            )
        ]
    )
    titulo = f"Total de Devolução (Dia) — {MESES_LABEL[mes - 1]}/{ano}"
    return _finalizar_figura(fig, titulo, height=CHART_HEIGHT_DIA)


def grafico_impacto_por_mes(
    mes: int,
    ano: int,
    rows: list[tuple[int, float]] | None = None,
) -> go.Figure:
    if rows is None:
        rows = dashboard_repository.impacto_financeiro_por_mes(ano, ate_mes=mes)
    mapa = {m: v for m, v in rows}
    meses_visiveis = list(range(1, mes + 1))
    labels = [MESES_LABEL[i - 1][:3] for i in meses_visiveis]
    valores = [mapa.get(i, 0.0) for i in meses_visiveis]
    cores = [
        COR_FINANCEIRO if i == mes else COR_FINANCEIRO_MUTED
        for i in meses_visiveis
    ]

    rotulos = [_rotulo_moeda(v, decimais=False) for v in valores]
    fig = go.Figure(
        data=[
            _barra(
                labels,
                valores,
                rotulos,
                cores,
                "%{x}<br><b>R$ %{y:,.0f}</b><extra></extra>",
            )
        ]
    )
    titulo = f"Impacto Financeiro (Mês) — {MESES_LABEL[mes - 1]}/{ano}"
    return _finalizar_figura(fig, titulo)


def grafico_devolucoes_por_mes(
    mes: int,
    ano: int,
    rows: list[tuple[int, int]] | None = None,
) -> go.Figure:
    """Barras por mês no ano — até o mês filtrado; mês selecionado em destaque."""
    if rows is None:
        rows = dashboard_repository.devolucoes_por_mes_no_ano(ano, ate_mes=mes)
    mapa = {m: t for m, t in rows}
    meses_visiveis = list(range(1, mes + 1))
    labels = [MESES_LABEL[i - 1][:3] for i in meses_visiveis]
    valores = [mapa.get(i, 0) for i in meses_visiveis]
    cores = [
        COR_DEVOLUCOES if i == mes else COR_DEVOLUCOES_MUTED
        for i in meses_visiveis
    ]

    rotulos = [_rotulo_int(v) for v in valores]
    fig = go.Figure(
        data=[
            _barra(
                labels,
                valores,
                rotulos,
                cores,
                "%{x}<br><b>%{y}</b> devoluções<extra></extra>",
            )
        ]
    )
    titulo = f"Total de Devolução (Mês) — {MESES_LABEL[mes - 1]}/{ano}"
    return _finalizar_figura(fig, titulo)


@st.cache_data(ttl=TTL_DASHBOARD, show_spinner=False)
def carregar_dashboard(mes: int, ano: int) -> dict[str, Any]:
    cards_raw = dashboard_repository.obter_cards_periodo(mes, ano)
    return {
        "cards": _cards_formatados(cards_raw),
        "mes": mes,
        "ano": ano,
    }


@st.cache_data(ttl=TTL_DASHBOARD, show_spinner=False)
def carregar_listview_dashboard(mes: int, ano: int, busca: str = "") -> pd.DataFrame:
    rows = listar_devolucoes_periodo_dashboard(mes, ano, busca=busca)
    return preparar_listview_dashboard(rows)


@st.cache_data(ttl=TTL_DASHBOARD, show_spinner=False)
def obter_graficos_cache(mes: int, ano: int) -> dict[str, dict[str, Any]]:
    from core.perf_monitor import track

    with track("dashboard", f"graficos_{mes}_{ano}"):
        agg = dashboard_repository.obter_agregacoes_graficos(mes, ano)
    return {
        "devolucoes_dia": grafico_devolucoes_por_dia(
            mes, ano, agg["por_dia"]
        ).to_dict(),
        "impacto_mes": grafico_impacto_por_mes(
            mes, ano, agg["impacto_mes"]
        ).to_dict(),
        "devolucoes_mes": grafico_devolucoes_por_mes(
            mes, ano, agg["por_mes_ano"]
        ).to_dict(),
    }


def obter_graficos(mes: int, ano: int) -> dict[str, go.Figure]:
    graficos = obter_graficos_cache(mes, ano)
    return {chave: go.Figure(fig) for chave, fig in graficos.items()}


@st.cache_data(ttl=TTL_DASHBOARD, show_spinner=False)
def export_pdf_dashboard_cache(
    mes_label: str,
    ano: int,
    busca: str,
    usuario: str,
    rows_tuple: tuple[dict[str, Any], ...],
) -> bytes:
    from services.export_dashboard_service import export_listagem_pdf_bytes

    rows = [_deserializar_devolucao_row(d) for d in rows_tuple]
    return export_listagem_pdf_bytes(
        rows,
        mes=mes_label,
        ano=ano,
        busca=busca,
        usuario_exportador=usuario,
    )


@st.cache_data(ttl=TTL_DASHBOARD, show_spinner=False)
def export_excel_dashboard_cache(
    rows_tuple: tuple[dict[str, Any], ...],
) -> bytes:
    from services.export_dashboard_service import export_listagem_excel_bytes

    rows = [_deserializar_devolucao_row(d) for d in rows_tuple]
    return export_listagem_excel_bytes(rows)
