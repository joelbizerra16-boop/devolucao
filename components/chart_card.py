"""Container visual premium para gráficos Plotly do dashboard."""

from __future__ import annotations

import streamlit as st

from core.theme import RADIUS_LG, SHADOW_SUBTLE

_CHART_CSS_INJECTED = False


def inject_dashboard_charts_css() -> None:
    global _CHART_CSS_INJECTED
    if _CHART_CSS_INJECTED:
        return
    st.markdown(
        f"""
        <style>
        .dash-chart-shell {{
            background: #111827;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: {RADIUS_LG};
            padding: 0.85rem 1rem;
            box-shadow: {SHADOW_SUBTLE};
            margin-bottom: 0.65rem;
            overflow: hidden;
            font-family: 'Inter', sans-serif;
        }}
        .dash-chart-shell [data-testid="stPlotlyChart"] {{
            background: rgba(17, 24, 39, 0.95) !important;
            border-radius: {RADIUS_LG};
        }}
        .dash-chart-shell [data-testid="stPlotlyChart"] > div {{
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    _CHART_CSS_INJECTED = True


def render_plotly_in_card(fig, key: str) -> None:
    """Renderiza gráfico Plotly dentro de card corporativo."""
    inject_dashboard_charts_css()
    st.markdown('<div class="dash-chart-shell">', unsafe_allow_html=True)
    st.plotly_chart(
        fig,
        use_container_width=True,
        key=key,
        config={"displayModeBar": False},
    )
    st.markdown("</div>", unsafe_allow_html=True)
