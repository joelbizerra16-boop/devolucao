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
TYPE_KPI = "1.625rem"              # 26px — valor KPI unificado (-7% vs 1.75rem)
TYPE_KPI_MONEY = "1.625rem"
TYPE_KPI_IMPACTO = "1.625rem"
TYPE_KPI_DEVOLUCOES = "1.625rem"
TYPE_KPI_WIDE = "0.8125rem"      # principal motivo (consultar / legado)
TYPE_KPI_PRINCIPAL_MOTIVO = "0.65rem"  # dashboard — ~20% menor que TYPE_KPI_WIDE
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

# Larguras corporativas (px) — proporção 190:390:270:110:140:180:250:130
LISTVIEW_COL_DATA = 190
LISTVIEW_COL_MOTIVO = 390
LISTVIEW_COL_TRATATIVA = 270
LISTVIEW_COL_NF = 110
LISTVIEW_COL_VALOR = 140
LISTVIEW_COL_COD = 180
LISTVIEW_COL_VENDEDOR = 250
LISTVIEW_COL_ACOES = 130
LISTVIEW_GRID_MIN_WIDTH = (
    LISTVIEW_COL_DATA
    + LISTVIEW_COL_MOTIVO
    + LISTVIEW_COL_TRATATIVA
    + LISTVIEW_COL_NF
    + LISTVIEW_COL_VALOR
    + LISTVIEW_COL_COD
    + LISTVIEW_COL_VENDEDOR
    + LISTVIEW_COL_ACOES
)  # 1620px

# Grid fixo desktop — header e linhas idênticos
LISTVIEW_GRID_COLUMNS = (
    f"{LISTVIEW_COL_DATA}px {LISTVIEW_COL_MOTIVO}px {LISTVIEW_COL_TRATATIVA}px "
    f"{LISTVIEW_COL_NF}px {LISTVIEW_COL_VALOR}px {LISTVIEW_COL_COD}px "
    f"{LISTVIEW_COL_VENDEDOR}px {LISTVIEW_COL_ACOES}px"
)
# Proporções fr para viewports < LISTVIEW_GRID_MIN_WIDTH (mesma razão)
LISTVIEW_GRID_COLUMNS_MD = (
    "minmax(96px, 1.12fr) minmax(130px, 2.05fr) minmax(120px, 1.72fr) "
    "minmax(72px, 0.66fr) minmax(88px, 0.84fr) minmax(100px, 1.08fr) "
    "minmax(120px, 1.5fr) minmax(72px, 0.78fr)"
)
LISTVIEW_ROW_MIN_HEIGHT = "0"
LISTVIEW_ROW_PADDING = "0 0.5rem"
LISTVIEW_ROW_CLAMP_LINE_HEIGHT = "1.22"
LISTVIEW_HEADER_MIN_HEIGHT = "1.625rem"
LISTVIEW_HEADER_PADDING = "0.25rem 0.5rem"
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
