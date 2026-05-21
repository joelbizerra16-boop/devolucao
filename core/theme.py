"""
Tokens de tipografia e espaçamento — refinamento premium (sem alterar paleta).
"""

from __future__ import annotations

from pathlib import Path

FONT_FAMILY = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
FONT_IMPORT_URL = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"
)

FONT_WEIGHT_REGULAR = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_SEMIBOLD = 600

# Escala tipográfica enterprise (rem)
TYPE_XS = "0.6875rem"      # 11px — labels, captions
TYPE_SM = "0.8125rem"      # 13px — corpo secundário
TYPE_BASE = "0.875rem"     # 14px — corpo
TYPE_MD = "0.9375rem"      # 15px — subtítulos
TYPE_LG = "1.125rem"       # 18px — títulos de seção
TYPE_XL = "1.25rem"        # 20px — page header
TYPE_KPI = "1.375rem"      # 22px — valores KPI
TYPE_KPI_SM = "1.125rem"   # 18px — KPI compacto

LINE_HEIGHT_TIGHT = "1.2"
LINE_HEIGHT_NORMAL = "1.45"
LINE_HEIGHT_RELAXED = "1.55"

RADIUS_SM = "8px"
RADIUS_MD = "10px"
RADIUS_LG = "12px"

SHADOW_CARD = "0 1px 2px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.18)"
SHADOW_CARD_HOVER = "0 2px 8px rgba(0,0,0,0.16), 0 8px 24px rgba(0,0,0,0.22)"
SHADOW_SUBTLE = "0 1px 3px rgba(0,0,0,0.14)"


def load_asset_styles() -> str:
    """Carrega assets/styles.css (tipografia e refinamentos globais)."""
    path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")
