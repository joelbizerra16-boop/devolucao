"""Repositório — agregações analíticas do dashboard."""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any, Optional

from sqlalchemy import extract, func

from core.db import get_session
from core.orm_serialize import devolucao_para_dict
from core.search_utils import aplicar_busca_query
from database.models import Devolucao


def _intervalo_mes(ano: int, mes: int) -> tuple[date, date]:
    ultimo_dia = monthrange(ano, mes)[1]
    return date(ano, mes, 1), date(ano, mes, ultimo_dia)


def _filtro_mes_ano(q, mes: int, ano: int):
    """Intervalo fechado — usa índice em data_devolucao (sem extract no WHERE)."""
    inicio, fim = _intervalo_mes(ano, mes)
    return q.filter(
        Devolucao.data_devolucao >= inicio,
        Devolucao.data_devolucao <= fim,
    )


def _filtro_ano_ate_mes(q, ano: int, ate_mes: int):
    inicio = date(ano, 1, 1)
    fim = date(ano, ate_mes, monthrange(ano, ate_mes)[1])
    return q.filter(
        Devolucao.data_devolucao >= inicio,
        Devolucao.data_devolucao <= fim,
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


def obter_agregacoes_graficos(mes: int, ano: int) -> dict[str, Any]:
    """Uma sessão para os três conjuntos de dados dos gráficos."""
    with get_session() as session:
        rows_dia = (
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

        rows_impacto = (
            _filtro_ano_ate_mes(
                session.query(
                    extract("month", Devolucao.data_devolucao).label("mes"),
                    func.coalesce(func.sum(Devolucao.valor_nf), 0.0).label("total"),
                ),
                ano,
                mes,
            )
            .group_by(extract("month", Devolucao.data_devolucao))
            .order_by(extract("month", Devolucao.data_devolucao).asc())
            .all()
        )

        rows_dev_mes = (
            _filtro_ano_ate_mes(
                session.query(
                    extract("month", Devolucao.data_devolucao).label("mes"),
                    func.count(Devolucao.id).label("total"),
                ),
                ano,
                mes,
            )
            .group_by(extract("month", Devolucao.data_devolucao))
            .order_by(extract("month", Devolucao.data_devolucao).asc())
            .all()
        )

    return {
        "por_dia": [(r[0], int(r[1] or 0)) for r in rows_dia if r[0] is not None],
        "impacto_mes": [
            (int(r[0]), float(r[1] or 0)) for r in rows_impacto if r[0] is not None
        ],
        "por_mes_ano": [
            (int(r[0]), int(r[1] or 0)) for r in rows_dev_mes if r[0] is not None
        ],
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
    if ate_mes is None:
        ate_mes = 12
    with get_session() as session:
        rows = (
            _filtro_ano_ate_mes(
                session.query(
                    extract("month", Devolucao.data_devolucao).label("mes"),
                    func.coalesce(func.sum(Devolucao.valor_nf), 0.0).label("total"),
                ),
                ano,
                ate_mes,
            )
            .group_by(extract("month", Devolucao.data_devolucao))
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
    if ate_mes is None:
        ate_mes = 12
    with get_session() as session:
        rows = (
            _filtro_ano_ate_mes(
                session.query(
                    extract("month", Devolucao.data_devolucao).label("mes"),
                    func.count(Devolucao.id).label("total"),
                ),
                ano,
                ate_mes,
            )
            .group_by(extract("month", Devolucao.data_devolucao))
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
) -> list[dict[str, Any]]:
    with get_session() as session:
        q = _filtro_mes_ano(session.query(Devolucao), mes, ano)
        q = aplicar_busca_query(q, busca)
        rows = (
            q.order_by(Devolucao.data_devolucao.desc(), Devolucao.id.desc())
            .limit(limit)
            .all()
        )
        return [devolucao_para_dict(r) for r in rows]
