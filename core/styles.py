"""
Estilos globais — tema corporativo dark ERP/WMS.
"""

from __future__ import annotations

import streamlit as st

# Paleta corporativa
COLORS = {
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "bg_card": "#1c2333",
    "border": "#30363d",
    "accent": "#1f6feb",
    "accent_hover": "#388bfd",
    "success": "#3fb950",
    "warning": "#d29922",
    "danger": "#f85149",
    "text": "#e6edf3",
    "text_muted": "#8b949e",
}


def _base_css() -> str:
    return f"""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .stApp {{
            background: linear-gradient(160deg, {COLORS["bg_primary"]} 0%, {COLORS["bg_secondary"]} 100%);
        }}

        section.main .block-container {{
            position: relative;
            z-index: 2;
        }}
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
            min-height: 2.25rem !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
        }}
        .login-title {{
            color: {COLORS["text"]};
            font-size: 1.2rem;
            font-weight: 700;
            text-align: center;
            margin: 0 0 0.2rem 0;
            line-height: 1.25;
        }}
        .login-subtitle {{
            color: {COLORS["text_muted"]};
            text-align: center;
            font-size: 0.88rem;
            margin: 0;
            line-height: 1.25;
        }}
        .login-module-name {{
            color: {COLORS["text_muted"]};
            font-weight: 600;
            letter-spacing: 0.06em;
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
            border-radius: 8px;
            font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_global_css() -> None:
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
            padding-top: 1.5rem;
            max-width: 100%;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
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
            padding-top: 1rem;
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
            border-radius: 12px;
            padding: 1rem 1.25rem;
            box-shadow: 0 4px 24px rgba(0,0,0,0.25);
        }}
        div[data-testid="stMetric"] label {{
            color: {COLORS["text_muted"]} !important;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
            color: {COLORS["text"]} !important;
            font-weight: 700;
        }}

        /* Dataframes */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {COLORS["border"]};
            border-radius: 10px;
            overflow: hidden;
        }}

        /* Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
            background: {COLORS["bg_card"]} !important;
            border-color: {COLORS["border"]} !important;
            color: {COLORS["text"]} !important;
            border-radius: 8px !important;
        }}

        /* Botão primário */
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {COLORS["accent"]}, #1158c7);
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.55rem 1.5rem;
            transition: all 0.2s ease;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: linear-gradient(135deg, {COLORS["accent_hover"]}, {COLORS["accent"]});
            box-shadow: 0 4px 16px rgba(31, 111, 235, 0.4);
        }}

        /* Cards customizados — altura uniforme na linha */
        div[data-testid="stHorizontalBlock"]:has(.op-card) {{
            align-items: stretch !important;
        }}
        div[data-testid="column"]:has(.op-card) > div {{
            display: flex !important;
            flex-direction: column !important;
            height: 100% !important;
        }}
        div[data-testid="column"]:has(.op-card) [data-testid="stMarkdown"] {{
            flex: 1 1 auto !important;
            display: flex !important;
            flex-direction: column !important;
        }}
        div[data-testid="column"]:has(.op-card) [data-testid="stMarkdown"] > div {{
            flex: 1 1 auto !important;
            display: flex !important;
            flex-direction: column !important;
        }}
        .op-card {{
            background: {COLORS["bg_card"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 14px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 0.5rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            transition: transform 0.15s ease, border-color 0.15s ease;
            box-sizing: border-box;
            min-height: 7.75rem;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }}
        .op-card:hover {{
            border-color: {COLORS["accent"]};
            transform: translateY(-2px);
        }}
        .op-card-title {{
            color: {COLORS["text_muted"]};
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin: 0 0 0.35rem 0;
        }}
        .op-card-value {{
            color: {COLORS["text"]};
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
            line-height: 1.1;
            flex: 1 1 auto;
        }}
        .op-card-sub {{
            display: block;
            font-size: 0.85rem;
            font-weight: 500;
            color: {COLORS["text_muted"]};
            line-height: 1.25;
            min-height: 1.15rem;
            margin-top: 0.2rem;
        }}
        .op-card-sub-placeholder {{
            visibility: hidden;
        }}
        .op-card-accent-pendente {{ border-left: 4px solid {COLORS["warning"]}; }}
        .op-card-accent-conferencia {{ border-left: 4px solid {COLORS["accent"]}; }}
        .op-card-accent-finalizada {{ border-left: 4px solid {COLORS["success"]}; }}
        .op-card-accent-coleta {{ border-left: 4px solid {COLORS["danger"]}; }}

        .page-header {{
            margin-bottom: 1.5rem;
        }}
        .page-header h1 {{
            color: {COLORS["text"]};
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0;
        }}
        .page-header p {{
            color: {COLORS["text_muted"]};
            margin: 0.25rem 0 0 0;
            font-size: 0.95rem;
        }}

        .badge-status {{
            display: inline-block;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_listview_premium_css() -> None:
    """Estilos da listagem operacional premium (dashboard)."""
    st.markdown(
        f"""
        <style>
        .lista-premium {{
            background: transparent;
            border: none;
            border-radius: 0;
            box-shadow: none;
            overflow: visible;
            margin-top: 0.5rem;
        }}
        .lista-premium-header {{
            background: rgba(255,255,255,0.02);
            border-top: 1px solid rgba(255,255,255,0.08);
            border-bottom: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 0.42rem 0.28rem 0.38rem 0.28rem;
            margin-bottom: 0.8rem;
        }}
        .lista-premium-body {{
            display: flex;
            flex-direction: column;
            gap: 0.7rem;
        }}
        .lista-premium-body .lista-premium-row {{
            background: rgba(17,24,39,0.35);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 0.42rem 0.42rem;
            box-shadow: 0 10px 24px rgba(0,0,0,0.14);
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
        }}
        .lista-premium-body .lista-premium-row:last-child {{
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}
        .lista-premium-row:hover {{
            background: rgba(17,24,39,0.5);
            border-color: rgba(96, 165, 250, 0.22);
            box-shadow: 0 14px 34px rgba(59,130,246,0.12);
            transform: translateY(-1px);
        }}
        .lista-dash-th {{
            color: {COLORS["text_muted"]};
            font-size: 0.73rem;
            font-weight: 600;
            letter-spacing: 0.025em;
            margin: 0;
            text-transform: none;
        }}
        .lista-dash-th-acoes {{
            text-align: center !important;
        }}
        .lv-cell {{
            color: {COLORS["text"]};
            font-size: 0.9rem;
            line-height: 1.15;
            margin: 0;
            word-break: normal;
        }}
        .lv-cell-user {{
            line-height: 1.04;
            padding-right: 0.06rem;
            display: flex;
            flex-direction: column;
            gap: 0.12rem;
        }}
        .lv-meta-row {{
            display: flex;
            align-items: center;
            gap: 0.34rem;
            min-width: 0;
        }}
        .lv-meta-icon {{
            width: 1rem;
            min-width: 1rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: rgba(148, 163, 184, 0.75);
            font-size: 0.68rem;
            line-height: 1;
        }}
        .lv-cell-user .lv-date {{
            color: {COLORS["text"]};
            font-weight: 700;
            font-size: 0.82rem;
        }}
        .lv-cell-user .lv-name {{
            color: {COLORS["text_muted"]};
            font-size: 0.72rem;
            margin-top: 0;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }}
        .lv-cell-motivo {{
            font-weight: 600;
            color: rgba(248, 250, 252, 0.96);
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            line-height: 1.2;
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
            max-width: 220px;
            color: rgba(241, 245, 249, 0.94);
            white-space: normal;
            overflow: hidden;
            text-overflow: initial;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            line-height: 1.2;
        }}
        .lv-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 2rem;
            padding: 0.35rem 0.72rem;
            border-radius: 10px;
            font-size: 0.84rem;
            font-weight: 700;
            line-height: 1;
            white-space: nowrap;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .lv-badge-nf {{
            color: #93c5fd;
            background: rgba(59,130,246,0.10);
            border: 1px solid rgba(59,130,246,0.18);
        }}
        .lv-badge-valor {{
            color: #4ade80;
            background: rgba(34,197,94,0.10);
            border: 1px solid rgba(34,197,94,0.20);
            font-variant-numeric: tabular-nums;
        }}
        .lista-premium [data-testid="stHorizontalBlock"] {{
            align-items: center !important;
            gap: 0.18rem !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker),
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) {{
            flex: 0 0 3.65rem !important;
            width: 3.65rem !important;
            min-width: 3.65rem !important;
            max-width: 3.65rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            align-self: center !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"],
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"] {{
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.5rem !important;
            width: auto !important;
            min-width: 3.4rem !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"] > div,
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) [data-testid="stHorizontalBlock"] > div {{
            flex: 0 0 1.7rem !important;
            width: 1.7rem !important;
            min-width: 1.7rem !important;
            max-width: 1.7rem !important;
        }}
        div[data-testid="column"]:has(.lista-dash-col-acoes-marker) button,
        div[data-testid="stColumn"]:has(.lista-dash-col-acoes-marker) button {{
            width: 1.7rem !important;
            min-width: 1.7rem !important;
            height: 1.7rem !important;
            min-height: 1.7rem !important;
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
        @media (max-width: 1280px) {{
            .lv-cell {{
                font-size: 0.84rem;
            }}
            .lv-cell-vendedor {{
                max-width: 180px;
            }}
            .lv-badge {{
                padding: 0.32rem 0.58rem;
            }}
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
