"""Repositório — dados SAP importados."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from core.db import get_session, get_session_factory
from database.models import DadoSAP


def buscar_por_nf(nf_nfd: str) -> Optional[DadoSAP]:
    chave = nf_nfd.strip()
    if not chave:
        return None
    with get_session() as session:
        return session.query(DadoSAP).filter(DadoSAP.nf_nfd == chave).first()


def nf_existe(nf_nfd: str) -> bool:
    return buscar_por_nf(nf_nfd) is not None


def contar_registros() -> int:
    with get_session() as session:
        return session.query(DadoSAP).count()


def listar_todos_como_dicts() -> list[dict[str, Any]]:
    """Backup lógico da base vigente para rollback."""
    with get_session() as session:
        rows = session.query(DadoSAP).all()
        return [
            {
                "nf_nfd": r.nf_nfd,
                "data_emissao_nf": r.data_emissao_nf,
                "cod_cliente": r.cod_cliente,
                "cliente": r.cliente,
                "cidade": r.cidade,
                "bairro": r.bairro,
                "vendedor": r.vendedor,
                "valor_nf": r.valor_nf,
                "arquivo_origem": r.arquivo_origem,
                "data_importacao": r.data_importacao,
            }
            for r in rows
        ]


def substituir_base_completa(registros: list[dict[str, Any]]) -> int:
    """
    Remove todos os registros SAP e insere a nova base em transação única.
    """
    session = get_session_factory()()
    try:
        session.query(DadoSAP).delete()
        if registros:
            agora = datetime.utcnow()
            for item in registros:
                item.setdefault("data_importacao", agora)
            session.bulk_insert_mappings(DadoSAP, registros)
        session.commit()
        return len(registros)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
