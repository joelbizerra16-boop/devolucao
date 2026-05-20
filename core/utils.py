"""
Utilitários gerais e constantes de apresentação.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from core.database import StatusDevolucao

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

STATUS_LABELS = {
    StatusDevolucao.PENDENTE: "Pendente",
    StatusDevolucao.EM_CONFERENCIA: "Em conferência",
    StatusDevolucao.FINALIZADA: "Finalizada",
    StatusDevolucao.AGUARDANDO_COLETA: "Aguardando coleta",
}

STATUS_COLORS = {
    StatusDevolucao.PENDENTE: "#d29922",
    StatusDevolucao.EM_CONFERENCIA: "#1f6feb",
    StatusDevolucao.FINALIZADA: "#3fb950",
    StatusDevolucao.AGUARDANDO_COLETA: "#f85149",
}


def asset_path(filename: str) -> Optional[Path]:
    path = ASSETS_DIR / filename
    return path if path.exists() else None


def sidebar_logo_path() -> Optional[Path]:
    """Logo oficial da sidebar (raiz do projeto; fallback em assets/)."""
    for base in (BASE_DIR, ASSETS_DIR):
        path = base / "Logo_B.png"
        if path.exists():
            return path
    return asset_path("logo.png")


def format_datetime(value: Optional[datetime]) -> str:
    if value is None:
        return "—"
    return value.strftime("%d/%m/%Y %H:%M")


def calcular_horas_abertas(data_abertura: datetime, data_fim: Optional[datetime] = None) -> float:
    fim = data_fim or datetime.utcnow()
    delta = fim - data_abertura
    return round(delta.total_seconds() / 3600, 1)


def sla_status(horas_abertas: float, sla_horas: float) -> str:
    if horas_abertas <= sla_horas * 0.7:
        return "No prazo"
    if horas_abertas <= sla_horas:
        return "Atenção"
    return "Estourado"


def devolucoes_to_display_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "status" in out.columns:
        out["status"] = out["status"].map(
            lambda s: STATUS_LABELS.get(StatusDevolucao(s), s) if isinstance(s, str) else STATUS_LABELS.get(s, s)
        )
    for col in ("data_abertura", "data_conferencia", "data_finalizacao"):
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce").apply(
                lambda x: format_datetime(x) if pd.notna(x) else "—"
            )
    return out
