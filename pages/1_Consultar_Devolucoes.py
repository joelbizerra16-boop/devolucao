"""Consultar devoluções — busca e filtros."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.layout import safe_page_run
from views.consultar_devolucoes import render

safe_page_run(render, "Consultar Devoluções")
