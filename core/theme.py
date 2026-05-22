"""
Tokens de tipografia e espaçamento — refinamento premium global (paleta inalterada).
"""

from __future__ import annotations

import functools
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
TYPE_KPI = "1.875rem"            # base valores KPI (~30px)
TYPE_KPI_MONEY = "1.875rem"      # impacto financeiro
TYPE_KPI_IMPACTO = "1.875rem"    # R$ — legível sem dominar o card
TYPE_KPI_DEVOLUCOES = "2.125rem" # contagem — leve destaque vs impacto
TYPE_KPI_WIDE = "0.9375rem"      # principal motivo — abaixo dos números
TYPE_KPI_SM = TYPE_KPI_MONEY
TYPE_CARD_LABEL = "0.75rem"
KPI_CARD_MIN_HEIGHT = "7rem"
KPI_TITLE_VALUE_GAP = "0.5rem"
KPI_VALUE_LINE_HEIGHT = "1.05"
# Alturas fixas anti layout-shift (px)
KPI_VALUE_MIN_H_IMPACTO = "32px"
KPI_VALUE_MIN_H_DEVOLUCOES = "36px"
KPI_VALUE_MIN_H_WIDE = "18px"
LISTVIEW_VISIBLE_ROWS = 20
LISTVIEW_ROW_HEIGHT_PX = 44
LISTVIEW_ROW_GAP_PX = 7
LISTVIEW_SCROLL_PX = (
    LISTVIEW_VISIBLE_ROWS * LISTVIEW_ROW_HEIGHT_PX
    + (LISTVIEW_VISIBLE_ROWS - 1) * LISTVIEW_ROW_GAP_PX
)  # 1013px — ~20 linhas visíveis (antes: 52vh ≈ 50 linhas)
LISTVIEW_PAGE_SIZE = 50
# Grid fixo — mesmas proporções dos st.columns [0.8, 2.1, 0.8, 0.9, 1.0, 1.4, 0.55]
LISTVIEW_GRID_COLUMNS = (
    "minmax(96px, 10.6fr) minmax(180px, 27.8fr) minmax(72px, 10.6fr) "
    "minmax(84px, 11.9fr) minmax(92px, 13.2fr) minmax(120px, 18.5fr) "
    "minmax(64px, 7.3fr)"
)
LISTVIEW_ROW_MIN_HEIGHT = "2.75rem"

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


@functools.lru_cache(maxsize=1)
def load_asset_styles() -> str:
    """Carrega assets/styles.css (tipografia e refinamentos globais)."""
    path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")
