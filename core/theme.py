"""
Tokens de tipografia e espaçamento — design system enterprise dark ERP/WMS.
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
TYPE_KPI = "1.75rem"               # 28px — valor KPI (-12,5% vs 2rem)
TYPE_KPI_MONEY = "1.7rem"          # 27,2px — moeda impacto (-15%)
TYPE_KPI_IMPACTO = "1.7rem"
TYPE_KPI_DEVOLUCOES = "1.85rem"    # 29,6px — contagem (-13% vs 2.125rem)
TYPE_KPI_WIDE = "0.8125rem"      # principal motivo
TYPE_KPI_SM = TYPE_KPI_MONEY
TYPE_CARD_LABEL = "0.75rem"        # 12px — título KPI
KPI_CARD_MIN_HEIGHT = "6.5rem"
KPI_TITLE_VALUE_GAP = "0.4rem"
KPI_VALUE_LINE_HEIGHT = "1.15"
KPI_VALUE_MIN_H_IMPACTO = "36px"
KPI_VALUE_MIN_H_DEVOLUCOES = "36px"
KPI_VALUE_MIN_H_WIDE = "18px"

LISTVIEW_VISIBLE_ROWS = 20
LISTVIEW_ROW_HEIGHT_PX = 44
LISTVIEW_ROW_GAP_PX = 7
LISTVIEW_SCROLL_PX = (
    LISTVIEW_VISIBLE_ROWS * LISTVIEW_ROW_HEIGHT_PX
    + (LISTVIEW_VISIBLE_ROWS - 1) * LISTVIEW_ROW_GAP_PX
)
LISTVIEW_PAGE_SIZE = 50

# Larguras corporativas (px) — proporção 180:450:180:110:140:140:220:120
LISTVIEW_COL_DATA = 180
LISTVIEW_COL_MOTIVO = 450
LISTVIEW_COL_TRATATIVA = 180
LISTVIEW_COL_NF = 110
LISTVIEW_COL_VALOR = 140
LISTVIEW_COL_COD = 140
LISTVIEW_COL_VENDEDOR = 220
LISTVIEW_COL_ACOES = 120
LISTVIEW_GRID_MIN_WIDTH = (
    LISTVIEW_COL_DATA
    + LISTVIEW_COL_MOTIVO
    + LISTVIEW_COL_TRATATIVA
    + LISTVIEW_COL_NF
    + LISTVIEW_COL_VALOR
    + LISTVIEW_COL_COD
    + LISTVIEW_COL_VENDEDOR
    + LISTVIEW_COL_ACOES
)  # 1540px

# Grid fixo desktop — header e linhas idênticos
LISTVIEW_GRID_COLUMNS = (
    f"{LISTVIEW_COL_DATA}px {LISTVIEW_COL_MOTIVO}px {LISTVIEW_COL_TRATATIVA}px "
    f"{LISTVIEW_COL_NF}px {LISTVIEW_COL_VALOR}px {LISTVIEW_COL_COD}px "
    f"{LISTVIEW_COL_VENDEDOR}px {LISTVIEW_COL_ACOES}px"
)
# Proporções fr para viewports < 1540px úteis (mesma razão)
LISTVIEW_GRID_COLUMNS_MD = (
    "minmax(96px, 1.17fr) minmax(140px, 2.92fr) minmax(96px, 1.17fr) "
    "minmax(72px, 0.71fr) minmax(88px, 0.91fr) minmax(88px, 0.91fr) "
    "minmax(110px, 1.43fr) minmax(72px, 0.78fr)"
)
LISTVIEW_ROW_MIN_HEIGHT = "2.75rem"
LISTVIEW_ROW_PADDING = "0.5rem 0.75rem"
LISTVIEW_COL_GAP = "0.75rem"

LINE_HEIGHT_TIGHT = "1.25"
LINE_HEIGHT_NORMAL = "1.5"
LINE_HEIGHT_RELAXED = "1.55"

RADIUS_SM = "6px"
RADIUS_MD = "8px"
RADIUS_LG = "10px"

SHADOW_CARD = "0 1px 2px rgba(0,0,0,0.18)"
SHADOW_CARD_HOVER = "0 2px 6px rgba(0,0,0,0.22)"
SHADOW_SUBTLE = "0 1px 2px rgba(0,0,0,0.12)"

# Plotly — tipografia alinhada ao sistema
PLOTLY_FONT = FONT_FAMILY_PLAIN
PLOTLY_TITLE_SIZE = 14
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
