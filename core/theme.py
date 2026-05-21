"""
Tokens de tipografia e espaçamento — refinamento premium global (paleta inalterada).
"""

from __future__ import annotations

from pathlib import Path

FONT_FAMILY = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
FONT_FAMILY_PLAIN = "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
FONT_IMPORT_URL = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"
)

FONT_WEIGHT_REGULAR = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_SEMIBOLD = 600

# Escala tipográfica enterprise (rem)
TYPE_XS = "0.6875rem"       # 11px
TYPE_SM = "0.8125rem"       # 13px
TYPE_BASE = "0.875rem"      # 14px
TYPE_MD = "0.9375rem"       # 15px
TYPE_LG = "1.125rem"        # 18px
TYPE_XL = "1.25rem"         # 20px — page header
TYPE_KPI = "3.25rem"             # base (outros usos)
TYPE_KPI_MONEY = "3rem"          # base impacto
TYPE_KPI_IMPACTO = "6rem"        # 2× impacto (R$)
TYPE_KPI_DEVOLUCOES = "6.5rem"   # 2× devoluções (número)
TYPE_KPI_WIDE = "1.5rem"         # principal motivo (inalterado)
TYPE_KPI_SM = TYPE_KPI_MONEY  # compatibilidade
TYPE_CARD_LABEL = "0.75rem"   # 12px — rótulo do card
KPI_CARD_MIN_HEIGHT = "7rem"
KPI_TITLE_VALUE_GAP = "0.5rem"
LISTVIEW_SCROLL_PX = 480

LINE_HEIGHT_TIGHT = "1.2"
LINE_HEIGHT_NORMAL = "1.45"
LINE_HEIGHT_RELAXED = "1.55"

RADIUS_SM = "8px"
RADIUS_MD = "10px"
RADIUS_LG = "12px"

SHADOW_CARD = "0 1px 2px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.18)"
SHADOW_CARD_HOVER = "0 2px 8px rgba(0,0,0,0.16), 0 8px 24px rgba(0,0,0,0.22)"
SHADOW_SUBTLE = "0 1px 3px rgba(0,0,0,0.14)"

# Plotly — tipografia alinhada ao sistema
PLOTLY_FONT = FONT_FAMILY_PLAIN
PLOTLY_TITLE_SIZE = 15
PLOTLY_AXIS_SIZE = 11
PLOTLY_HOVER_SIZE = 12
PLOTLY_BAR_LABEL_SIZE = 11
PLOTLY_LEGEND_SIZE = 11


def load_asset_styles() -> str:
    """Carrega assets/styles.css (tipografia e refinamentos globais)."""
    path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")
