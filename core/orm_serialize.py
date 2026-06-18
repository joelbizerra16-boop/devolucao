"""Serialização de entidades ORM — uso dentro do `with get_session()` antes do close."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional


def _iso(val: Any) -> Any:
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    return val


def dado_sap_para_dict(row: Any) -> dict[str, Any]:
    """Payload seguro para cache Streamlit e uso fora da Session."""
    return {
        "nf_nfd": row.nf_nfd,
        "data_emissao_nf": _iso(row.data_emissao_nf),
        "cod_cliente": row.cod_cliente,
        "cliente": row.cliente,
        "cidade": row.cidade,
        "bairro": row.bairro,
        "vendedor": row.vendedor,
        "valor_nf": float(row.valor_nf) if row.valor_nf is not None else None,
        "arquivo_origem": getattr(row, "arquivo_origem", None),
        "data_importacao": _iso(getattr(row, "data_importacao", None)),
    }


def devolucao_para_dict(row: Any) -> dict[str, Any]:
    return {
        "id": int(row.id),
        "data_devolucao": _iso(row.data_devolucao),
        "usuario": row.usuario,
        "usuario_ultima_edicao": row.usuario_ultima_edicao,
        "motivo_devolucao": row.motivo_devolucao,
        "tratativa": getattr(row, "tratativa", None) or "Aguardando",
        "tratativa_atualizada_em": _iso(getattr(row, "tratativa_atualizada_em", None)),
        "tratativa_atualizada_por": getattr(row, "tratativa_atualizada_por", None),
        "nf_nfd": row.nf_nfd,
        "valor_nf": float(row.valor_nf) if row.valor_nf is not None else None,
        "cod_cliente": row.cod_cliente,
        "cliente": getattr(row, "cliente", None),
        "cidade": getattr(row, "cidade", None),
        "bairro": getattr(row, "bairro", None),
        "vendedor": row.vendedor,
        "observacao": getattr(row, "observacao", None),
        "data_emissao_nf": _iso(getattr(row, "data_emissao_nf", None)),
    }


def parse_iso_date(val: Any) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    try:
        return date.fromisoformat(str(val))
    except (TypeError, ValueError):
        return None


def parse_iso_datetime(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    texto = str(val).strip()
    if not texto:
        return None
    try:
        return datetime.fromisoformat(texto)
    except (TypeError, ValueError):
        return None
