"""Cards operacionais estilo ERP/WMS."""

from __future__ import annotations

import streamlit as st

from core.styles import COLORS
from core.theme import (
    KPI_VALUE_LINE_HEIGHT,
    KPI_VALUE_MIN_H_DEVOLUCOES,
    KPI_VALUE_MIN_H_IMPACTO,
    KPI_VALUE_MIN_H_WIDE,
    TYPE_KPI_DEVOLUCOES,
    TYPE_KPI_IMPACTO,
    TYPE_KPI_WIDE,
)

OPERATIONAL_CARD_CONFIG = [
    ("impacto_financeiro", "Impacto", "💰", "op-card-accent-pendente", COLORS["warning"]),
    ("devolucoes", "Devoluções", "📦", "op-card-accent-conferencia", COLORS["accent_light"]),
    ("principal_motivo", "Principal Motivo", "📊", "op-card-accent-finalizada", COLORS["success"]),
]

DASHBOARD_CARD_CONFIG = [
    ("impacto_financeiro", "Impacto", "💰", "op-card-accent-pendente", COLORS["warning"]),
    ("devolucoes", "Devoluções", "📦", "op-card-accent-conferencia", COLORS["accent_light"]),
    ("principal_motivo", "Principal Motivo", "📊", "op-card-accent-finalizada", COLORS["success"]),
]

def _render_card(
    col,
    key: str,
    label: str,
    icon: str,
    css_class: str,
    color: str,
    metricas: dict[str, str],
    *,
    wide: bool = False,
) -> None:
    valor = metricas.get(key, "—")
    sub = metricas.get(f"{key}_sub", "")
    if sub:
        sub_html = f'<span class="op-card-sub">{sub}</span>'
    else:
        sub_html = '<span class="op-card-sub op-card-sub-placeholder">&nbsp;</span>'
    value_class = "op-card-value"
    font_size = TYPE_KPI_IMPACTO
    min_h = KPI_VALUE_MIN_H_IMPACTO
    if key == "impacto_financeiro":
        value_class += " op-card-value--impacto"
        font_size = TYPE_KPI_IMPACTO
        min_h = KPI_VALUE_MIN_H_IMPACTO
    elif key == "devolucoes":
        value_class += " op-card-value--devolucoes"
        font_size = TYPE_KPI_DEVOLUCOES
        min_h = KPI_VALUE_MIN_H_DEVOLUCOES
    elif key == "principal_motivo" and wide:
        value_class += " op-card-value--wide"
        font_size = TYPE_KPI_WIDE
        min_h = KPI_VALUE_MIN_H_WIDE
    wrap = "word-wrap:break-word;" if wide else ""
    # font-size inline = primeiro paint estável (anti FOUC / font jump)
    height_lock = ""
    if key != "principal_motivo":
        height_lock = f"min-height:{min_h};max-height:{min_h};"
    elif wide:
        height_lock = f"min-height:{min_h};"
    value_style = (
        f"color:{color};"
        f"font-size:{font_size};"
        f"line-height:{KPI_VALUE_LINE_HEIGHT};"
        f"{height_lock}"
        f"margin:0;padding:0;"
        f"{wrap}"
    )
    with col:
        st.markdown(
            f"""
            <div class="op-card {css_class}">
                <p class="op-card-title">{icon} {label}</p>
                <p class="{value_class}" style="{value_style}">{valor}</p>
                {sub_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_cards_operacionais(metricas: dict[str, str], config: list) -> None:
    c1, c2, c3 = st.columns([1, 1, 2])
    for col, (key, label, icon, css_class, color) in zip([c1, c2, c3], config):
        _render_card(
            col, key, label, icon, css_class, color, metricas,
            wide=(key == "principal_motivo"),
        )


def render_operational_cards(metricas: dict[str, str]) -> None:
    """Três cards — Consultar Devoluções (1:1:2, altura uniforme)."""
    _render_cards_operacionais(metricas, OPERATIONAL_CARD_CONFIG)


def render_dashboard_cards(metricas: dict[str, str]) -> None:
    """Três cards — Dashboard (mesmo layout, rótulos analíticos)."""
    _render_cards_operacionais(metricas, DASHBOARD_CARD_CONFIG)


def render_kpi_row(kpis: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total de devoluções", kpis.get("total", 0))
    with c2:
        st.metric("Tempo médio (h)", f"{kpis.get('tempo_medio_horas', 0):.1f}")
    with c3:
        st.metric("SLA no prazo", f"{kpis.get('sla_no_prazo_pct', 0):.1f}%")
    with c4:
        estourado = kpis.get("sla_estourado_pct", 0)
        st.metric("SLA estourado", f"{estourado:.1f}%", delta=None, delta_color="inverse")
