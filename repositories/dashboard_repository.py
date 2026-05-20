"""Repositório — agregações analíticas do dashboard."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from sqlalchemy import extract, func, or_

from core.db import get_session
from database.models import Devolucao


def _filtro_mes_ano(q, mes: int, ano: int):
    return q.filter(
        extract("year", Devolucao.data_devolucao) == ano,
        extract("month", Devolucao.data_devolucao) == mes,
    )


def listar_anos_disponiveis() -> list[int]:
    with get_session() as session:
        rows = (
            session.query(extract("year", Devolucao.data_devolucao).label("ano"))
            .distinct()
            .order_by(extract("year", Devolucao.data_devolucao).desc())
            .all()
        )
    anos = sorted({int(r[0]) for r in rows if r[0] is not None}, reverse=True)
    return anos


def obter_periodo_padrao() -> tuple[int, int]:
    with get_session() as session:
        ultima = session.query(func.max(Devolucao.data_devolucao)).scalar()
    if isinstance(ultima, date):
        return ultima.month, ultima.year
    from datetime import datetime

    hoje = datetime.now()
    return hoje.month, hoje.year


def obter_cards_periodo(mes: int, ano: int) -> dict[str, Any]:
    with get_session() as session:
        base = _filtro_mes_ano(session.query(Devolucao), mes, ano)
        soma_valor = base.with_entities(
            func.coalesce(func.sum(Devolucao.valor_nf), 0.0)
        ).scalar()
        total = base.with_entities(func.count(Devolucao.id)).scalar() or 0

        motivo_row = (
            _filtro_mes_ano(
                session.query(
                    Devolucao.motivo_devolucao,
                    func.count(Devolucao.id).label("total"),
                ),
                mes,
                ano,
            )
            .filter(
                Devolucao.motivo_devolucao.isnot(None),
                Devolucao.motivo_devolucao != "",
            )
            .group_by(Devolucao.motivo_devolucao)
            .order_by(func.count(Devolucao.id).desc())
            .first()
        )

    motivo: Optional[str] = None
    motivo_qtd = 0
    if motivo_row:
        motivo = str(motivo_row[0]).strip() or None
        motivo_qtd = int(motivo_row[1] or 0)

    return {
        "soma_valor_nf": float(soma_valor or 0),
        "total_devolucoes": int(total),
        "principal_motivo": motivo,
        "principal_motivo_qtd": motivo_qtd,
    }


def devolucoes_por_dia(mes: int, ano: int) -> list[tuple[date, int]]:
    with get_session() as session:
        rows = (
            _filtro_mes_ano(
                session.query(
                    Devolucao.data_devolucao,
                    func.count(Devolucao.id).label("total"),
                ),
                mes,
                ano,
            )
            .group_by(Devolucao.data_devolucao)
            .order_by(Devolucao.data_devolucao.asc())
            .all()
        )
    return [(r[0], int(r[1] or 0)) for r in rows if r[0] is not None]


def impacto_financeiro_por_mes(
    ano: int, ate_mes: int | None = None
) -> list[tuple[int, float]]:
    with get_session() as session:
        q = session.query(
            extract("month", Devolucao.data_devolucao).label("mes"),
            func.coalesce(func.sum(Devolucao.valor_nf), 0.0).label("total"),
        ).filter(extract("year", Devolucao.data_devolucao) == ano)
        if ate_mes is not None:
            q = q.filter(extract("month", Devolucao.data_devolucao) <= ate_mes)
        rows = (
            q.group_by(extract("month", Devolucao.data_devolucao))
            .order_by(extract("month", Devolucao.data_devolucao).asc())
            .all()
        )
    return [(int(r[0]), float(r[1] or 0)) for r in rows if r[0] is not None]


def impacto_financeiro_por_dia(mes: int, ano: int) -> list[tuple[date, float]]:
    with get_session() as session:
        rows = (
            _filtro_mes_ano(
                session.query(
                    Devolucao.data_devolucao,
                    func.coalesce(func.sum(Devolucao.valor_nf), 0.0).label("total"),
                ),
                mes,
                ano,
            )
            .group_by(Devolucao.data_devolucao)
            .order_by(Devolucao.data_devolucao.asc())
            .all()
        )
    return [(r[0], float(r[1] or 0)) for r in rows if r[0] is not None]


def devolucoes_por_mes_no_ano(ano: int, ate_mes: int | None = None) -> list[tuple[int, int]]:
    """Contagem por mês no ano; se ate_mes informado, só meses 1..ate_mes."""
    with get_session() as session:
        q = session.query(
            extract("month", Devolucao.data_devolucao).label("mes"),
            func.count(Devolucao.id).label("total"),
        ).filter(extract("year", Devolucao.data_devolucao) == ano)
        if ate_mes is not None:
            q = q.filter(extract("month", Devolucao.data_devolucao) <= ate_mes)
        rows = (
            q.group_by(extract("month", Devolucao.data_devolucao))
            .order_by(extract("month", Devolucao.data_devolucao).asc())
            .all()
        )
    return [(int(r[0]), int(r[1] or 0)) for r in rows if r[0] is not None]


def motivos_no_periodo(mes: int, ano: int) -> list[tuple[str, int]]:
    with get_session() as session:
        rows = (
            _filtro_mes_ano(
                session.query(
                    Devolucao.motivo_devolucao,
                    func.count(Devolucao.id).label("total"),
                ),
                mes,
                ano,
            )
            .filter(
                Devolucao.motivo_devolucao.isnot(None),
                Devolucao.motivo_devolucao != "",
            )
            .group_by(Devolucao.motivo_devolucao)
            .order_by(func.count(Devolucao.id).desc())
            .all()
        )
    return [(str(r[0]).strip(), int(r[1] or 0)) for r in rows if r[0]]


def listar_periodo(
    mes: int,
    ano: int,
    busca: str = "",
    limit: int = 500,
) -> list[Devolucao]:
    with get_session() as session:
        q = _filtro_mes_ano(session.query(Devolucao), mes, ano)
        if busca:
            termo = f"%{busca.strip()}%"
            q = q.filter(
                or_(
                    Devolucao.usuario.ilike(termo),
                    Devolucao.nf_nfd.ilike(termo),
                    Devolucao.motivo_devolucao.ilike(termo),
                    Devolucao.cod_cliente.ilike(termo),
                    Devolucao.vendedor.ilike(termo),
                    Devolucao.cliente.ilike(termo),
                )
            )
        return (
            q.order_by(Devolucao.data_devolucao.desc(), Devolucao.id.desc())
            .limit(limit)
            .all()
        )
