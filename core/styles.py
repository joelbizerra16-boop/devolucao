"""
Estilos globais — tema corporativo dark ERP/WMS (refinamento tipográfico premium).
"""

from __future__ import annotations

import streamlit as st

from core.theme import (
    FONT_FAMILY,
    FONT_IMPORT_URL,
    FONT_WEIGHT_MEDIUM,
    FONT_WEIGHT_REGULAR,
    FONT_WEIGHT_SEMIBOLD,
    LINE_HEIGHT_NORMAL,
    LINE_HEIGHT_TIGHT,
    RADIUS_LG,
    RADIUS_MD,
    RADIUS_SM,
    SHADOW_CARD,
    SHADOW_CARD_HOVER,
    SHADOW_SUBTLE,
    TYPE_BASE,
    KPI_CARD_MIN_HEIGHT,
    KPI_TITLE_VALUE_GAP,
    KPI_VALUE_LINE_HEIGHT,
    KPI_VALUE_MIN_H_DEVOLUCOES,
    KPI_VALUE_MIN_H_IMPACTO,
    KPI_VALUE_MIN_H_WIDE,
    LISTVIEW_GRID_COLUMNS,
    LISTVIEW_GRID_COLUMNS_MD,
    LISTVIEW_GRID_MIN_WIDTH,
    LISTVIEW_ROW_MIN_HEIGHT,
    LISTVIEW_ROW_PADDING,
    LISTVIEW_ROW_CLAMP_LINE_HEIGHT,
    LISTVIEW_HEADER_MIN_HEIGHT,
    LISTVIEW_HEADER_PADDING,
    LISTVIEW_COL_GAP,
    LISTVIEW_COL_COD,
    LISTVIEW_COL_VALOR,
    LISTVIEW_COL_VENDEDOR,
    LISTVIEW_SCROLL_PX,
    TYPE_CARD_LABEL,
    TYPE_KPI,
    TYPE_KPI_DEVOLUCOES,
    TYPE_KPI_IMPACTO,
    TYPE_KPI_MONEY,
    TYPE_KPI_SM,
    TYPE_KPI_WIDE,
    TYPE_LG,
    TYPE_MD,
    TYPE_SM,
    TYPE_XL,
    TYPE_XS,
    load_asset_styles,
)

# Paleta corporativa
COLORS = {
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "bg_card": "#1c2333",
    "border": "#30363d",
    "accent": "#1f6feb",
    "accent_hover": "#388bfd",
    "accent_light": "#79c0ff",
    "success": "#3fb950",
    "warning": "#d29922",
    "danger": "#f85149",
    "text": "#e6edf3",
    "text_muted": "#8b949e",
}


def _base_css() -> str:
    asset_css = load_asset_styles()
    return f"""
        @import url('{FONT_IMPORT_URL}');

        html, body, [class*="css"] {{
            font-family: {FONT_FAMILY};
            font-size: {TYPE_BASE};
            font-weight: {FONT_WEIGHT_REGULAR};
            line-height: {LINE_HEIGHT_NORMAL};
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        .stApp {{
            background: {COLORS["bg_primary"]};
        }}

        section.main .block-container {{
            position: relative;
            z-index: 2;
        }}

        {asset_css}
"""


def inject_login_css(background_url: str | None = None) -> None:
    """CSS da tela de login — conteúdo sempre acima do fundo escuro."""
    bg_rule = ""
    if background_url:
        bg_rule = f"""
        .stApp {{
            background: linear-gradient(rgba(13,17,23,0.88), rgba(13,17,23,0.94)),
                        url('{background_url}') center/cover no-repeat fixed !important;
        }}
        """
    st.markdown(
        f"""
        <style>
        {_base_css()}
        {bg_rule}

        /* Login: oculta sidebar e garante formulário visível */
        section[data-testid="stSidebar"] {{
            display: none !important;
        }}
        section.main {{
            z-index: 2;
        }}
        .main .block-container {{
            padding-top: clamp(2rem, 8vh, 5rem);
            padding-bottom: 2rem;
            max-width: 920px;
            margin: 0 auto;
        }}
        /* Linha principal: logo + login lado a lado */
        div[data-testid="stHorizontalBlock"]:has(.login-brand-col):has(.login-form-col) {{
            width: fit-content !important;
            max-width: calc(100% - 2rem) !important;
            margin-left: 20% !important;
            margin-right: auto !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 0.75rem !important;
        }}
        @media (max-width: 900px) {{
            div[data-testid="stHorizontalBlock"]:has(.login-brand-col):has(.login-form-col) {{
                margin-left: 8% !important;
            }}
        }}
        div[data-testid="stHorizontalBlock"]:has(.login-brand-col):has(.login-form-col) > div[data-testid="column"]:first-child,
        div[data-testid="stHorizontalBlock"]:has(.login-brand-col):has(.login-form-col) > div[data-testid="stColumn"]:first-child {{
            flex: 0 0 auto !important;
            width: auto !important;
            max-width: 300px !important;
            min-width: unset !important;
            display: flex !important;
            justify-content: flex-end !important;
            align-items: center !important;
            padding: 0 !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(.login-brand-col):has(.login-form-col) > div[data-testid="column"]:last-child,
        div[data-testid="stHorizontalBlock"]:has(.login-brand-col):has(.login-form-col) > div[data-testid="stColumn"]:last-child {{
            flex: 0 0 auto !important;
            width: auto !important;
            max-width: 320px !important;
            min-width: unset !important;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            padding: 0 !important;
        }}
        div[data-testid="column"]:has(.login-brand-col),
        div[data-testid="stColumn"]:has(.login-brand-col) {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}
        div[data-testid="column"]:has(.login-brand-col) [data-testid="stImage"],
        div[data-testid="stColumn"]:has(.login-brand-col) [data-testid="stImage"] {{
            display: flex !important;
            justify-content: flex-end !important;
            width: 100% !important;
            max-width: 300px !important;
            margin: 0 !important;
        }}
        div[data-testid="column"]:has(.login-brand-col) img,
        div[data-testid="stColumn"]:has(.login-brand-col) img {{
            display: block !important;
            max-width: 300px !important;
            width: 100% !important;
            height: auto !important;
            margin: 0 !important;
        }}
        div[data-testid="column"]:has(.login-form-col),
        div[data-testid="stColumn"]:has(.login-form-col) {{
            flex: 0 0 auto !important;
            max-width: 320px !important;
            width: auto !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}
        div[data-testid="column"]:has(.login-form-col) > div,
        div[data-testid="stColumn"]:has(.login-form-col) > div {{
            width: 100% !important;
            max-width: 320px !important;
        }}
        .login-form-card {{
            width: 100%;
            margin: 0 0 0.5rem 0;
            padding: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            text-align: center;
        }}
        div[data-testid="column"]:has(.login-form-col) [data-testid="stForm"],
        div[data-testid="stColumn"]:has(.login-form-col) [data-testid="stForm"] {{
            width: 100% !important;
            border: 1px solid {COLORS["border"]} !important;
            border-radius: 12px !important;
            padding: 0.75rem 1rem 0.8rem 1rem !important;
            background: {COLORS["bg_card"]} !important;
            box-shadow: 0 16px 48px rgba(0,0,0,0.4);
            box-sizing: border-box !important;
        }}
        div[data-testid="column"]:has(.login-form-col) [data-testid="stForm"] [data-testid="stVerticalBlock"],
        div[data-testid="stColumn"]:has(.login-form-col) [data-testid="stForm"] [data-testid="stVerticalBlock"] {{
            gap: 0.45rem !important;
        }}
        div[data-testid="column"]:has(.login-form-col) [data-testid="stTextInput"] label,
        div[data-testid="stColumn"]:has(.login-form-col) [data-testid="stTextInput"] label {{
            font-size: 0.85rem !important;
        }}
        div[data-testid="column"]:has(.login-form-col) [data-testid="stTextInput"] input,
        div[data-testid="stColumn"]:has(.login-form-col) [data-testid="stTextInput"] input {{
            padding: 0.45rem 0.7rem !important;
            min-height: 2.1rem !important;
            font-size: 0.9rem !important;
        }}
        div[data-testid="column"]:has(.login-form-col) [data-testid="stFormSubmitButton"] button,
        div[data-testid="stColumn"]:has(.login-form-col) [data-testid="stFormSubmitButton"] button {{
            min-height: 2.2rem !important;
            font-size: {TYPE_BASE} !important;
            font-weight: {FONT_WEIGHT_MEDIUM} !important;
        }}
        .login-title {{
            color: {COLORS["text"]};
            font-size: {TYPE_LG};
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            text-align: center;
            margin: 0 0 0.2rem 0;
            line-height: {LINE_HEIGHT_TIGHT};
            letter-spacing: -0.02em;
        }}
        .login-subtitle {{
            color: {COLORS["text_muted"]};
            text-align: center;
            font-size: {TYPE_SM};
            margin: 0;
            line-height: {LINE_HEIGHT_NORMAL};
            font-weight: {FONT_WEIGHT_REGULAR};
        }}
        .login-module-name {{
            color: {COLORS["text_muted"]};
            font-weight: {FONT_WEIGHT_MEDIUM};
            letter-spacing: 0.05em;
            font-size: {TYPE_XS};
        }}
        #MainMenu, footer {{
            visibility: hidden;
            height: 0;
        }}
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}
        .stTextInput input {{
            background: {COLORS["bg_secondary"]} !important;
            border-color: {COLORS["border"]} !important;
            color: {COLORS["text"]} !important;
        }}
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {COLORS["accent"]}, #1158c7);
            border: none;
            border-radius: {RADIUS_SM};
            font-weight: {FONT_WEIGHT_MEDIUM};
            font-size: {TYPE_BASE};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _operational_cards_premium_css() -> str:
    """Cards KPI — enterprise dark (SAP Fiori / Salesforce style)."""
    return f"""
        /* Cards KPI — layout uniforme */
        div[data-testid="stHorizontalBlock"]:has(.op-card) {{
            align-items: stretch !important;
            gap: 0.75rem !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(.op-card-dashboard-row) {{
            gap: 0.75rem !important;
        }}
        @media (max-width: 1280px) {{
            div[data-testid="stHorizontalBlock"]:has(.op-card-dashboard-row) {{
                gap: 0.5rem !important;
            }}
            .op-card {{
                padding: 0.65rem 0.85rem !important;
            }}
        }}
        @media (max-width: 992px) {{
            div[data-testid="stHorizontalBlock"]:has(.op-card-dashboard-row) {{
                flex-wrap: wrap !important;
            }}
            div[data-testid="stHorizontalBlock"]:has(.op-card-dashboard-row) > div[data-testid="column"],
            div[data-testid="stHorizontalBlock"]:has(.op-card-dashboard-row) > div[data-testid="stColumn"] {{
                min-width: 18% !important;
                flex: 1 1 18% !important;
            }}
            div[data-testid="stHorizontalBlock"]:has(.op-card-dashboard-row) > div[data-testid="column"]:last-child,
            div[data-testid="stHorizontalBlock"]:has(.op-card-dashboard-row) > div[data-testid="stColumn"]:last-child {{
                min-width: 38% !important;
                flex: 2 1 38% !important;
            }}
        }}
        div[data-testid="column"]:has(.op-card) > div,
        div[data-testid="stColumn"]:has(.op-card) > div {{
            display: flex !important;
            flex-direction: column !important;
            height: 100% !important;
        }}
        div[data-testid="column"]:has(.op-card) [data-testid="stMarkdown"],
        div[data-testid="stColumn"]:has(.op-card) [data-testid="stMarkdown"] {{
            flex: 1 1 auto !important;
            display: flex !important;
            flex-direction: column !important;
            height: 100% !important;
            min-height: {KPI_CARD_MIN_HEIGHT} !important;
            max-height: {KPI_CARD_MIN_HEIGHT} !important;
        }}
        div[data-testid="column"]:has(.op-card) [data-testid="stMarkdown"] > div,
        div[data-testid="stColumn"]:has(.op-card) [data-testid="stMarkdown"] > div {{
            flex: 1 1 auto !important;
            display: flex !important;
            flex-direction: column !important;
            height: 100% !important;
            width: 100% !important;
        }}

        .op-card {{
            position: relative;
            background: {COLORS["bg_card"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS_LG};
            margin-bottom: 0;
            box-shadow: {SHADOW_SUBTLE};
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
            box-sizing: border-box;
            min-height: {KPI_CARD_MIN_HEIGHT};
            max-height: {KPI_CARD_MIN_HEIGHT};
            height: {KPI_CARD_MIN_HEIGHT};
            width: 100%;
            padding: 0.7rem 1rem 0.65rem;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            flex: 1 1 auto;
            overflow: hidden;
        }}
        .op-card::before,
        .op-card::after {{
            display: none;
        }}
        .op-card:hover {{
            border-color: rgba(139, 148, 158, 0.45);
            box-shadow: {SHADOW_CARD};
        }}

        .op-card-title {{
            color: {COLORS["text_muted"]};
            font-size: {TYPE_CARD_LABEL};
            font-weight: {FONT_WEIGHT_MEDIUM};
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 0 0 {KPI_TITLE_VALUE_GAP} 0;
            line-height: 1.3;
            flex: 0 0 auto;
        }}
        [data-testid="stMarkdownContainer"] .op-card p.op-card-title,
        .op-card p.op-card-title {{
            font-size: {TYPE_CARD_LABEL} !important;
            font-weight: {FONT_WEIGHT_MEDIUM} !important;
            line-height: 1.3 !important;
        }}
        [data-testid="stMarkdownContainer"] .op-card p.op-card-value,
        .op-card p.op-card-value {{
            font-size: {TYPE_KPI} !important;
            font-weight: {FONT_WEIGHT_SEMIBOLD} !important;
            line-height: {KPI_VALUE_LINE_HEIGHT} !important;
            letter-spacing: -0.02em !important;
            margin: 0 !important;
            padding: 0 !important;
            flex: 0 0 auto;
            overflow: hidden;
            text-overflow: ellipsis;
            text-shadow: none !important;
        }}
        .op-card-value--impacto,
        p.op-card-value--impacto {{
            font-size: {TYPE_KPI_IMPACTO} !important;
            line-height: {KPI_VALUE_LINE_HEIGHT} !important;
            min-height: {KPI_VALUE_MIN_H_IMPACTO} !important;
            max-height: {KPI_VALUE_MIN_H_IMPACTO} !important;
            letter-spacing: -0.02em !important;
            text-shadow: none !important;
        }}
        .op-card-value--devolucoes,
        p.op-card-value--devolucoes {{
            font-size: {TYPE_KPI_DEVOLUCOES} !important;
            line-height: {KPI_VALUE_LINE_HEIGHT} !important;
            min-height: {KPI_VALUE_MIN_H_DEVOLUCOES} !important;
            max-height: {KPI_VALUE_MIN_H_DEVOLUCOES} !important;
            letter-spacing: -0.02em !important;
            text-shadow: none !important;
        }}
        .op-card-value--wide,
        p.op-card-value--wide {{
            font-size: {TYPE_KPI_WIDE} !important;
            line-height: 1.35 !important;
            min-height: {KPI_VALUE_MIN_H_WIDE} !important;
            max-height: none !important;
            font-weight: {FONT_WEIGHT_SEMIBOLD} !important;
            letter-spacing: -0.01em !important;
            text-shadow: none !important;
            white-space: normal;
        }}
        .op-card-sub {{
            display: block;
            font-size: {TYPE_SM};
            font-weight: {FONT_WEIGHT_REGULAR};
            color: {COLORS["text_muted"]};
            line-height: 1.4;
            margin: auto 0 0 0;
            padding-top: 0.3rem;
            flex: 0 0 auto;
        }}
        .op-card-sub-placeholder {{
            visibility: hidden;
            display: block;
            font-size: {TYPE_SM};
            line-height: 1.4;
            margin: auto 0 0 0;
            padding-top: 0.3rem;
            min-height: 1.35em;
            flex: 0 0 auto;
        }}

        .op-card-accent-pendente {{
            border-left: 3px solid {COLORS["warning"]};
        }}
        .op-card-accent-conferencia {{
            border-left: 3px solid {COLORS["accent_light"]};
        }}
        .op-card-accent-finalizada {{
            border-left: 3px solid {COLORS["success"]};
        }}
        .op-card-accent-coleta {{
            border-left: 3px solid {COLORS["danger"]};
        }}
    """


def inject_operational_cards_premium_css() -> None:
    """Cards KPI — reinjetado a cada render (multipage Streamlit / switch_page após login)."""
    st.markdown(
        f"<style>{_operational_cards_premium_css()}</style>",
        unsafe_allow_html=True,
    )


def inject_global_css() -> None:
    if st.session_state.get("_css_global_injected"):
        return
    st.session_state["_css_global_injected"] = True
    st.markdown(
        f"""
        <style>
        {_base_css()}

        #MainMenu, footer {{
            visibility: hidden;
            height: 0;
        }}

        /* Botão recolher/expandir menu lateral */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        button[kind="header"] {{
            visibility: visible !important;
            display: flex !important;
        }}

        /* Oculta navegação automática do Streamlit; usa menu customizado */
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}

        .main .block-container {{
            padding-top: 1.25rem;
            max-width: 100%;
            padding-left: 1.25rem;
            padding-right: 1.25rem;
        }}


        /* Sidebar — permite recolher normalmente */
        section[data-testid="stSidebar"] {{
            background: {COLORS["bg_secondary"]};
            border-right: 1px solid {COLORS["border"]};
        }}
        section[data-testid="stSidebar"][aria-expanded="true"] {{
            min-width: 18rem;
        }}
        section[data-testid="stSidebar"] .block-container {{
            padding-top: 0.85rem;
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }}

        section[data-testid="stSidebar"] [data-testid="stPageLink"] {{
            margin-bottom: 0.15rem;
        }}
        section[data-testid="stSidebar"] [data-testid="stPageLink"] a {{
            font-size: {TYPE_BASE} !important;
            font-weight: {FONT_WEIGHT_MEDIUM} !important;
            padding: 0.35rem 0.5rem !important;
            border-radius: {RADIUS_SM};
        }}
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
            font-size: {TYPE_SM} !important;
            font-weight: {FONT_WEIGHT_REGULAR} !important;
        }}

        /* Logo oficial — centralizada na sidebar */
        section[data-testid="stSidebar"] .block-container > div:first-child {{
            margin-top: 20px !important;
            margin-bottom: 25px !important;
        }}
        section[data-testid="stSidebar"] .block-container > div:first-child [data-testid="stHorizontalBlock"] {{
            justify-content: center !important;
            align-items: center !important;
            width: 100% !important;
        }}
        section[data-testid="stSidebar"] .block-container > div:first-child [data-testid="column"] {{
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            min-width: 0 !important;
        }}
        section[data-testid="stSidebar"] .block-container > div:first-child [data-testid="stImage"] {{
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            margin: 0 auto !important;
        }}
        section[data-testid="stSidebar"] .block-container > div:first-child [data-testid="stImage"] img {{
            width: 95px !important;
            max-width: 95px !important;
            height: auto !important;
            object-fit: contain;
            display: block;
            margin: 0 auto;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            background: transparent !important;
        }}

        /* ListView / tabela responsiva */
        div[data-testid="stDataFrame"],
        div[data-testid="stDataFrame"] > div {{
            width: 100% !important;
        }}
        div[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {{
            width: 100% !important;
        }}

        /* Métricas / cards nativos */
        div[data-testid="stMetric"] {{
            background: {COLORS["bg_card"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS_LG};
            padding: 0.75rem 1rem;
            box-shadow: {SHADOW_SUBTLE};
        }}
        div[data-testid="stMetric"] label {{
            color: {COLORS["text_muted"]} !important;
            font-size: {TYPE_XS} !important;
            font-weight: {FONT_WEIGHT_MEDIUM} !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
            color: {COLORS["text"]} !important;
            font-weight: {FONT_WEIGHT_SEMIBOLD} !important;
            font-size: {TYPE_KPI} !important;
            letter-spacing: -0.02em;
        }}

        /* Dataframes */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS_MD};
            overflow: hidden;
        }}

        /* Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
            background: {COLORS["bg_card"]} !important;
            border-color: {COLORS["border"]} !important;
            color: {COLORS["text"]} !important;
            border-radius: {RADIUS_SM} !important;
            font-size: {TYPE_BASE} !important;
            font-weight: {FONT_WEIGHT_REGULAR} !important;
        }}

        /* Botão primário */
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {COLORS["accent"]}, #1158c7);
            border: none;
            border-radius: {RADIUS_SM};
            font-weight: {FONT_WEIGHT_MEDIUM};
            font-size: {TYPE_BASE};
            padding: 0.45rem 1.25rem;
            transition: all 0.2s ease;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: linear-gradient(135deg, {COLORS["accent_hover"]}, {COLORS["accent"]});
            box-shadow: 0 4px 16px rgba(31, 111, 235, 0.4);
        }}

        {_operational_cards_premium_css()}

        .page-header {{
            margin-bottom: 1.15rem;
        }}
        .page-header h1 {{
            color: {COLORS["text"]};
            font-size: {TYPE_XL};
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            margin: 0;
            letter-spacing: -0.025em;
            line-height: {LINE_HEIGHT_TIGHT};
        }}
        .page-header p {{
            color: {COLORS["text_muted"]};
            margin: 0.2rem 0 0 0;
            font-size: {TYPE_SM};
            font-weight: {FONT_WEIGHT_REGULAR};
            line-height: {LINE_HEIGHT_NORMAL};
        }}

        .badge-status {{
            display: inline-block;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            font-size: {TYPE_XS};
            font-weight: {FONT_WEIGHT_MEDIUM};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_listview_premium_css() -> None:
    """Estilos da listagem operacional — reinjetados a cada render (estabilidade Cloud/rerun)."""
    st.markdown(
        f"""
        <style>
        /* Escopo estável — grade corporativa enterprise */
        .lista-premium-stable {{
            width: 100%;
            max-width: 100%;
            margin-top: 0.5rem;
        }}
        .lista-premium-header {{
            background: {COLORS["bg_card"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS_LG} {RADIUS_LG} 0 0;
            padding: 0;
            margin-bottom: 0;
        }}
        .lista-premium-header-sticky {{
            position: sticky;
            top: 0;
            z-index: 3;
        }}
        /* Scroll — header + linhas compartilham largura de grade */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) {{
            max-height: {LISTVIEW_SCROLL_PX}px !important;
            height: {LISTVIEW_SCROLL_PX}px !important;
            overflow: hidden !important;
            border: 1px solid {COLORS["border"]} !important;
            border-radius: {RADIUS_LG} !important;
            background: {COLORS["bg_secondary"]} !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            > div[data-testid="stVerticalBlock"] {{
            display: flex !important;
            flex-direction: column !important;
            gap: 0 !important;
            max-height: {LISTVIEW_SCROLL_PX}px !important;
            height: 100% !important;
            min-height: 0 !important;
            overflow-y: auto !important;
            overflow-x: auto !important;
            padding-right: 0;
            scrollbar-gutter: stable;
            scrollbar-width: thin;
            scrollbar-color: rgba(139, 148, 158, 0.4) rgba(255, 255, 255, 0.04);
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            > div[data-testid="stVerticalBlock"]::-webkit-scrollbar {{
            width: 8px;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            > div[data-testid="stVerticalBlock"]::-webkit-scrollbar-track {{
            background: rgba(255, 255, 255, 0.04);
            border-radius: 8px;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            > div[data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {{
            background: rgba(139, 148, 158, 0.38);
            border-radius: 8px;
            border: 2px solid transparent;
            background-clip: padding-box;
        }}
        /* Grid fixo — header e linhas com mesma geometria ({LISTVIEW_GRID_MIN_WIDTH}px desktop) */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) {{
            display: grid !important;
            grid-template-columns: {LISTVIEW_GRID_COLUMNS} !important;
            column-gap: {LISTVIEW_COL_GAP} !important;
            row-gap: 0 !important;
            width: 100% !important;
            min-width: {LISTVIEW_GRID_MIN_WIDTH}px !important;
            max-width: none !important;
            box-sizing: border-box !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) {{
            align-items: center !important;
            min-height: {LISTVIEW_HEADER_MIN_HEIGHT} !important;
            padding: {LISTVIEW_HEADER_PADDING} !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) {{
            align-items: start !important;
            min-height: {LISTVIEW_ROW_MIN_HEIGHT} !important;
            height: auto !important;
            padding: {LISTVIEW_ROW_PADDING} !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) {{
            background: {COLORS["bg_card"]};
            border: none;
            border-bottom: 1px solid {COLORS["border"]};
            box-shadow: none;
            margin: 0;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            > div[data-testid="stVerticalBlock"] > * {{
            margin-block: 0 !important;
            padding-block: 0 !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="stVerticalBlock"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="stElementContainer"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="stMarkdownContainer"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="stMarkdown"] {{
            margin: 0 !important;
            padding: 0 !important;
            gap: 0 !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) {{
            background: transparent;
            border: none;
            border-radius: 0;
            box-shadow: none;
            margin: 0;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker):hover {{
            background: rgba(28, 35, 51, 0.55);
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            > div[data-testid="stVerticalBlock"] > div:has([data-testid="stHorizontalBlock"]:has(.lv-row-marker)),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            [data-testid="stElementContainer"]:has([data-testid="stHorizontalBlock"]:has(.lv-row-marker)) {{
            margin: 0 !important;
            padding: 0 !important;
        }}
        /* Divisor entre registros — linha cinza visível em toda a largura do grid */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) .lv-row-divider {{
            display: block;
            width: 100%;
            min-width: {LISTVIEW_GRID_MIN_WIDTH}px;
            height: 1px;
            margin: 0;
            padding: 0;
            border: 0;
            background: rgba(148, 163, 184, 0.35);
            box-sizing: border-box;
            pointer-events: none;
            flex-shrink: 0;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            > div[data-testid="stVerticalBlock"] > div:has(.lv-row-divider),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            [data-testid="stElementContainer"]:has(.lv-row-divider),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            [data-testid="stMarkdownContainer"]:has(.lv-row-divider),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            [data-testid="stMarkdown"]:has(.lv-row-divider) {{
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            min-width: {LISTVIEW_GRID_MIN_WIDTH}px !important;
            max-width: none !important;
            align-self: stretch !important;
            flex: 0 0 auto !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="column"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) [data-testid="column"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="stColumn"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) [data-testid="stColumn"] {{
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            flex: none !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) [data-testid="column"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) [data-testid="stColumn"] {{
            align-self: center !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="column"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="stColumn"] {{
            align-self: start !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="column"] > div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) [data-testid="column"] > div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="stColumn"] > div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) [data-testid="stColumn"] > div {{
            width: 100% !important;
            min-width: 0 !important;
        }}
        /* Valor, Cliente e Vendedor — largura mínima do grid (evita colisão de cabeçalho) */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(5),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(5) {{
            min-width: {LISTVIEW_COL_VALOR}px !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(6),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(6) {{
            min-width: {LISTVIEW_COL_COD}px !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(7),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(7) {{
            min-width: {LISTVIEW_COL_VENDEDOR}px !important;
        }}
        .lv-row-marker,
        .lv-table-header-marker {{
            display: none !important;
            width: 0 !important;
            height: 0 !important;
            overflow: hidden !important;
            position: absolute !important;
            pointer-events: none !important;
        }}
        .lista-dash-th {{
            color: {COLORS["text_muted"]};
            font-size: {TYPE_XS};
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            letter-spacing: 0.03em;
            margin: 0;
            text-transform: uppercase;
            line-height: 1.2;
            white-space: nowrap;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
        }}
        /* Cabeçalho — texto centralizado dentro da faixa do grid, sem transbordar */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(4),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(5),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(6),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(7),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(8) {{
            justify-content: stretch !important;
        }}
        .lista-dash-th-acoes,
        .lista-dash-th-center {{
            text-align: center !important;
            white-space: nowrap !important;
        }}
        /* Colunas NF, Valor, Cod, Vendedor, Ações — alinhamento central */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(4),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(5),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(4),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(5),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(6),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(6),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(7),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(7),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(8),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(8) {{
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(4) [data-testid="stMarkdown"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(5) [data-testid="stMarkdown"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(4) [data-testid="stMarkdown"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(5) [data-testid="stMarkdown"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(6) [data-testid="stMarkdown"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(6) [data-testid="stMarkdown"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:nth-child(7) [data-testid="stMarkdown"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:nth-child(7) [data-testid="stMarkdown"] {{
            width: 100% !important;
            display: flex !important;
            justify-content: center !important;
        }}
        .lv-col-nf,
        .lv-col-valor,
        .lv-col-cod {{
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            text-align: center;
            width: 100%;
        }}
        .lv-cell {{
            color: {COLORS["text"]};
            font-size: {TYPE_BASE};
            font-weight: {FONT_WEIGHT_REGULAR};
            line-height: 1.2;
            margin: 0;
            word-break: normal;
        }}
        .lv-cell-user {{
            line-height: 1;
            padding-right: 0;
            display: flex;
            flex-direction: column;
            gap: 0;
            min-width: 0;
        }}
        .lv-meta-row {{
            display: flex;
            align-items: center;
            gap: 0.18rem;
            min-width: 0;
        }}
        .lv-meta-row-date {{
            white-space: nowrap;
        }}
        .lv-meta-icon {{
            width: 0.75rem;
            min-width: 0.75rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: rgba(148, 163, 184, 0.75);
            font-size: 0.62rem;
            line-height: 1;
        }}
        .lv-cell-user .lv-date {{
            color: {COLORS["text"]};
            font-weight: {FONT_WEIGHT_MEDIUM};
            font-size: {TYPE_SM};
            line-height: 1.15;
            white-space: nowrap;
        }}
        .lv-cell-user .lv-name {{
            color: {COLORS["text_muted"]};
            font-size: {TYPE_XS};
            font-weight: {FONT_WEIGHT_REGULAR};
            line-height: 1.15;
            margin-top: 0;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }}
        .lv-cell-motivo {{
            font-weight: {FONT_WEIGHT_MEDIUM};
            color: {COLORS["text"]};
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: normal;
            line-height: {LISTVIEW_ROW_CLAMP_LINE_HEIGHT};
            max-height: calc({LISTVIEW_ROW_CLAMP_LINE_HEIGHT}em * 2);
            max-width: 100%;
        }}
        .lv-cell-tratativa {{
            font-weight: {FONT_WEIGHT_REGULAR};
            color: {COLORS["text"]};
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: normal;
            line-height: {LISTVIEW_ROW_CLAMP_LINE_HEIGHT};
            max-height: calc({LISTVIEW_ROW_CLAMP_LINE_HEIGHT}em * 2);
            max-width: 100%;
        }}
        .lv-cell-truncate {{
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            display: block;
            width: 100%;
        }}
        .lv-cell-vendedor {{
            max-width: 100%;
            color: {COLORS["text"]};
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: normal;
            line-height: {LISTVIEW_ROW_CLAMP_LINE_HEIGHT};
            max-height: calc({LISTVIEW_ROW_CLAMP_LINE_HEIGHT}em * 2);
            text-align: center;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            [data-testid="stHorizontalBlock"]:has(.lv-row-marker) p.lv-cell,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker)
            [data-testid="stHorizontalBlock"]:has(.lv-row-marker) .lv-cell-user {{
            margin: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }}
        .lv-badge {{
            display: inline-block;
            align-items: center;
            justify-content: center;
            min-height: auto;
            padding: 0;
            border-radius: 0;
            font-size: {TYPE_SM};
            font-weight: {FONT_WEIGHT_MEDIUM};
            line-height: {LINE_HEIGHT_TIGHT};
            white-space: nowrap;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            background: transparent;
            border: none;
        }}
        .lv-badge-nf {{
            color: {COLORS["accent_light"]};
        }}
        .lv-badge-valor {{
            color: {COLORS["success"]};
            font-variant-numeric: tabular-nums;
        }}
        /* Tooltip — title nativo + camada estilizada (fonte ampliada) */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) .lv-tip[data-lv-tip] {{
            position: relative;
            cursor: default;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) .lv-tip[data-lv-tip]::after {{
            content: attr(data-lv-tip);
            position: absolute;
            left: 0;
            top: calc(100% + 0.35rem);
            z-index: 9999;
            display: block;
            width: max-content;
            max-width: min(24rem, 90vw);
            padding: 10px 14px;
            font-size: 15px;
            font-weight: {FONT_WEIGHT_REGULAR};
            line-height: 1.45;
            color: {COLORS["text"]};
            background: {COLORS["bg_card"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS_SM};
            box-shadow: {SHADOW_CARD};
            white-space: normal;
            word-break: break-word;
            pointer-events: none;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.12s ease;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) .lv-tip[data-lv-tip]:hover {{
            z-index: 9998;
            overflow: visible;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) .lv-tip[data-lv-tip]:hover::after {{
            opacity: 1;
            visibility: visible;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) > div:has(.lv-tip:hover),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) > div:has(.lv-tip:hover) {{
            overflow: visible !important;
            z-index: 9997;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="stMarkdownContainer"]:has(.lv-tip:hover),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) [data-testid="stMarkdownContainer"]:has(.lv-tip:hover) {{
            overflow: visible !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker):has(.lv-tip:hover) > div[data-testid="stVerticalBlock"] {{
            overflow: visible !important;
        }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker) [data-testid="stMarkdownContainer"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) [data-testid="stMarkdownContainer"] {{
            margin: 0 !important;
            padding: 0 !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker),
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) {{
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            align-self: center !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"],
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"] {{
            display: grid !important;
            grid-template-columns: 1.25rem 1.25rem !important;
            column-gap: 0.16rem !important;
            align-items: center !important;
            justify-content: center !important;
            width: auto !important;
            min-width: 0 !important;
            max-width: 100% !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"] > div,
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"] > div {{
            flex: 0 0 1.25rem !important;
            width: 1.25rem !important;
            min-width: 1.25rem !important;
            max-width: 1.25rem !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker) button,
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) button {{
            width: 1.25rem !important;
            min-width: 1.25rem !important;
            height: 1.25rem !important;
            min-height: 1.25rem !important;
            padding: 0 !important;
            border-radius: 7px !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            background: rgba(15,23,42,0.74) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: none !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker) button svg,
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) button svg {{
            width: 0.9rem !important;
            height: 0.9rem !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"] > div:last-child button:hover,
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"] > div:last-child button:hover {{
            background: rgba(248, 81, 73, 0.18) !important;
            border-color: rgba(248, 81, 73, 0.5) !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"] > div:first-child button:hover,
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"] > div:first-child button:hover {{
            background: rgba(47, 128, 237, 0.2) !important;
            border-color: rgba(47, 128, 237, 0.5) !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker) button p {{
            display: none !important;
        }}
        .lista-dash-acoes-empty {{
            text-align: center;
            color: {COLORS["text_muted"]};
            margin: 0;
            font-size: 0.85rem;
        }}
        div[data-testid="column"]:has(.lista-dash-col-tratativa-marker) [data-testid="stHorizontalBlock"],
        div[data-testid="stColumn"]:has(.lista-dash-col-tratativa-marker) [data-testid="stHorizontalBlock"] {{
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) 1.25rem !important;
            align-items: center !important;
            gap: 0.12rem !important;
            width: 100% !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-tratativa-marker) [data-testid="stHorizontalBlock"] > div:last-child,
        div[data-testid="stColumn"]:has(.lista-dash-col-tratativa-marker) [data-testid="stHorizontalBlock"] > div:last-child {{
            flex: 0 0 1.25rem !important;
            width: 1.25rem !important;
            min-width: 1.25rem !important;
            max-width: 1.25rem !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-tratativa-marker) button,
        div[data-testid="stColumn"]:has(.lista-dash-col-tratativa-marker) button {{
            width: 1.25rem !important;
            min-width: 1.25rem !important;
            height: 1.25rem !important;
            min-height: 1.25rem !important;
            padding: 0 !important;
        }}
        @media (max-width: {LISTVIEW_GRID_MIN_WIDTH}px) {{
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-row-marker),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.lista-premium-scroller-marker) [data-testid="stHorizontalBlock"]:has(.lv-table-header-marker) {{
                grid-template-columns: {LISTVIEW_GRID_COLUMNS_MD} !important;
                min-width: 0 !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_tratativa_dialog_css() -> None:
    """Modal compacto — Editar Tratativa."""
    if st.session_state.get("_css_tratativa_dialog_injected"):
        return
    st.session_state["_css_tratativa_dialog_injected"] = True
    st.markdown(
        """
        <style>
        [data-testid="stDialog"] [data-testid="stForm"] {
            padding-top: 0.15rem !important;
        }
        [data-testid="stDialog"] [data-testid="stForm"] [data-testid="stVerticalBlock"] {
            gap: 0.45rem !important;
        }
        [data-testid="stDialog"] .tratativa-dialog-section {
            margin: 0.35rem 0 0.1rem 0;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            color: rgba(148, 163, 184, 0.92);
        }
        [data-testid="stDialog"] [data-testid="stTextArea"] textarea {
            min-height: 5.25rem !important;
            max-height: 7rem !important;
        }
        [data-testid="stDialog"] [data-testid="stCaptionContainer"] {
            margin-top: -0.15rem !important;
        }
        @media (max-width: 640px) {
            [data-testid="stDialog"] [data-testid="stForm"] [data-testid="column"] {
                min-width: 0 !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_dashboard_export_toolbar_css() -> None:
    """Botões ícone PDF/Excel alinhados à barra de filtros da listagem operacional."""
    if st.session_state.get("_css_dash_export_injected"):
        return
    st.session_state["_css_dash_export_injected"] = True
    st.markdown(
        f"""
        <style>
        div[data-testid="column"]:has(.dash-export-marker-pdf),
        div[data-testid="column"]:has(.dash-export-marker-xlsx),
        div[data-testid="stColumn"]:has(.dash-export-marker-pdf),
        div[data-testid="stColumn"]:has(.dash-export-marker-xlsx) {{
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-end !important;
        }}
        div[data-testid="column"]:has(.dash-export-marker-pdf) [data-testid="stDownloadButton"] button,
        div[data-testid="column"]:has(.dash-export-marker-xlsx) [data-testid="stDownloadButton"] button,
        div[data-testid="stColumn"]:has(.dash-export-marker-pdf) [data-testid="stDownloadButton"] button,
        div[data-testid="stColumn"]:has(.dash-export-marker-xlsx) [data-testid="stDownloadButton"] button {{
            width: 2.35rem !important;
            min-width: 2.35rem !important;
            height: 2.35rem !important;
            min-height: 2.35rem !important;
            padding: 0 !important;
            border-radius: {RADIUS_MD} !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            background: rgba(15,23,42,0.72) !important;
            backdrop-filter: blur(8px);
            transition: background 0.18s ease, border-color 0.18s ease, transform 0.12s ease;
            box-shadow: {SHADOW_SUBTLE} !important;
        }}
        div[data-testid="column"]:has(.dash-export-marker-pdf) [data-testid="stDownloadButton"] button:hover,
        div[data-testid="stColumn"]:has(.dash-export-marker-pdf) [data-testid="stDownloadButton"] button:hover {{
            background: rgba(47, 128, 237, 0.22) !important;
            border-color: rgba(47, 128, 237, 0.45) !important;
            transform: translateY(-1px);
        }}
        div[data-testid="column"]:has(.dash-export-marker-xlsx) [data-testid="stDownloadButton"] button:hover,
        div[data-testid="stColumn"]:has(.dash-export-marker-xlsx) [data-testid="stDownloadButton"] button:hover {{
            background: rgba(63, 185, 80, 0.18) !important;
            border-color: rgba(63, 185, 80, 0.42) !important;
            transform: translateY(-1px);
        }}
        div[data-testid="column"]:has(.dash-export-marker-pdf) [data-testid="stDownloadButton"] button svg,
        div[data-testid="column"]:has(.dash-export-marker-xlsx) [data-testid="stDownloadButton"] button svg,
        div[data-testid="stColumn"]:has(.dash-export-marker-pdf) [data-testid="stDownloadButton"] button svg,
        div[data-testid="stColumn"]:has(.dash-export-marker-xlsx) [data-testid="stDownloadButton"] button svg {{
            width: 1.05rem !important;
            height: 1.05rem !important;
        }}
        div[data-testid="column"]:has(.dash-export-marker-pdf) [data-testid="stDownloadButton"] button p,
        div[data-testid="column"]:has(.dash-export-marker-xlsx) [data-testid="stDownloadButton"] button p,
        div[data-testid="stColumn"]:has(.dash-export-marker-pdf) [data-testid="stDownloadButton"] button p,
        div[data-testid="stColumn"]:has(.dash-export-marker-xlsx) [data-testid="stDownloadButton"] button p {{
            display: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="page-header"><h1>{title}</h1>{sub}</div>',
        unsafe_allow_html=True,
    )
