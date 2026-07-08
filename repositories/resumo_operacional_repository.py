"""Repositório — agregações analíticas do Resumo Operacional de Devoluções."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import and_, func, or_

from core.db import get_session
from core.tratativa_constants import TRATATIVA_FILTRO_TODOS, TRATATIVA_PADRAO
from database.models import Devolucao
from repositories.dashboard_repository import _filtro_mes_ano

FILTRO_TODOS_CLIENTE = "Todos"
FILTRO_TODOS_MOTIVO = "Todos"
_COD_CLIENTE_VAZIO = "__SEM_COD__"


@dataclass(frozen=True)
class FiltrosResumo:
    mes: int
    ano: int
    cliente: str = FILTRO_TODOS_CLIENTE
    motivo: str = FILTRO_TODOS_MOTIVO
    tratativa: str = TRATATIVA_FILTRO_TODOS


def _col_tratativa_norm():
    return func.lower(func.trim(Devolucao.tratativa))


def _tratativa_vazia():
    return or_(
        Devolucao.tratativa.is_(None),
        func.trim(Devolucao.tratativa) == "",
    )


def _expr_recusado():
    col = _col_tratativa_norm()
    return and_(~_tratativa_vazia(), col.contains("recusad"))


def _expr_concluido():
    col = _col_tratativa_norm()
    return and_(
        ~_tratativa_vazia(),
        ~col.contains("recusad"),
        or_(col.contains("conclu"), col == "resolvido"),
    )


def _expr_em_analise():
    col = _col_tratativa_norm()
    return and_(
        ~_tratativa_vazia(),
        ~col.contains("recusad"),
        ~col.contains("conclu"),
        col != "resolvido",
        or_(col.contains("analise"), col.contains("análise")),
    )


def _expr_aguardando():
    """Alinhado a core.tratativa_utils.classificar_tratativa — categoria Aguardando."""
    return or_(
        _tratativa_vazia(),
        and_(~_expr_recusado(), ~_expr_concluido(), ~_expr_em_analise()),
    )


def _aplicar_filtro_tratativa_sql(q, tratativa: str):
    filtro = (tratativa or TRATATIVA_FILTRO_TODOS).strip()
    if not filtro or filtro == TRATATIVA_FILTRO_TODOS:
        return q
    if filtro == "Recusado":
        return q.filter(_expr_recusado())
    if filtro == "Concluído":
        return q.filter(_expr_concluido())
    if filtro == "Em Análise":
        return q.filter(_expr_em_analise())
    if filtro == "Aguardando":
        return q.filter(_expr_aguardando())
    if filtro.casefold() == TRATATIVA_PADRAO.casefold():
        return q.filter(_expr_aguardando())
    return q


def _cod_cliente_chave():
    return func.coalesce(
        func.nullif(func.trim(Devolucao.cod_cliente), ""),
        _COD_CLIENTE_VAZIO,
    )


def _aplicar_filtro_cliente(q, cliente: str):
    valor = (cliente or FILTRO_TODOS_CLIENTE).strip()
    if not valor or valor == FILTRO_TODOS_CLIENTE:
        return q
    if valor == _COD_CLIENTE_VAZIO:
        return q.filter(
            or_(
                Devolucao.cod_cliente.is_(None),
                func.trim(Devolucao.cod_cliente) == "",
            )
        )
    return q.filter(func.trim(Devolucao.cod_cliente) == valor)


def _aplicar_filtro_motivo(q, motivo: str):
    valor = (motivo or FILTRO_TODOS_MOTIVO).strip()
    if not valor or valor == FILTRO_TODOS_MOTIVO:
        return q
    return q.filter(func.trim(Devolucao.motivo_devolucao) == valor)


def _query_base(session, filtros: FiltrosResumo):
    q = _filtro_mes_ano(session.query(Devolucao), filtros.mes, filtros.ano)
    q = _aplicar_filtro_cliente(q, filtros.cliente)
    q = _aplicar_filtro_motivo(q, filtros.motivo)
    q = _aplicar_filtro_tratativa_sql(q, filtros.tratativa)
    return q


def _rotulo_cliente(cod: str, nome: Optional[str]) -> str:
    cod_txt = (cod or "").strip()
    nome_txt = (nome or "").strip()
    if cod_txt and cod_txt != _COD_CLIENTE_VAZIO:
        return f"{cod_txt} — {nome_txt}" if nome_txt else cod_txt
    return nome_txt or "(Sem código)"


def listar_opcoes_cliente(mes: int, ano: int) -> list[tuple[str, str]]:
    """Retorna (cod_cliente_chave, rótulo) para selectbox — somente período."""
    with get_session() as session:
        rows = (
            _filtro_mes_ano(
                session.query(
                    _cod_cliente_chave().label("cod"),
                    func.max(Devolucao.cliente).label("nome"),
                ),
                mes,
                ano,
            )
            .group_by(_cod_cliente_chave())
            .order_by(_cod_cliente_chave().asc())
            .all()
        )
    resultado: list[tuple[str, str]] = []
    for cod, nome in rows:
        chave = str(cod or _COD_CLIENTE_VAZIO)
        resultado.append((chave, _rotulo_cliente(chave, str(nome) if nome else None)))
    return resultado


def listar_opcoes_motivo(mes: int, ano: int) -> list[str]:
    with get_session() as session:
        rows = (
            _filtro_mes_ano(
                session.query(Devolucao.motivo_devolucao).distinct(),
                mes,
                ano,
            )
            .filter(
                Devolucao.motivo_devolucao.isnot(None),
                func.trim(Devolucao.motivo_devolucao) != "",
            )
            .order_by(Devolucao.motivo_devolucao.asc())
            .all()
        )
    return [str(r[0]).strip() for r in rows if r[0]]


def _calcular_ticket_medio(soma_valor: float, total: int) -> float:
    if total <= 0:
        return 0.0
    return float(soma_valor) / int(total)


def _calcular_media_diaria_valor(soma_valor: float, mes: int, ano: int) -> float:
    """Média diária financeira: valor total devolvido ÷ quantidade de dias do mês."""
    dias_mes = monthrange(ano, mes)[1]
    if dias_mes <= 0:
        return 0.0
    return float(soma_valor) / dias_mes


def obter_kpis(filtros: FiltrosResumo) -> dict[str, Any]:
    with get_session() as session:
        base = _query_base(session, filtros)
        total = int(base.with_entities(func.count(Devolucao.id)).scalar() or 0)
        soma_valor = float(
            base.with_entities(
                func.coalesce(func.sum(Devolucao.valor_nf), 0.0)
            ).scalar()
            or 0.0
        )

    ticket_medio = _calcular_ticket_medio(soma_valor, total)
    media_movel = _calcular_media_diaria_valor(
        soma_valor,
        filtros.mes,
        filtros.ano,
    )

    return {
        "total_devolucoes": total,
        "soma_valor_nf": soma_valor,
        "ticket_medio": ticket_medio,
        "media_movel_diaria": media_movel,
    }


def _top5_motivos(
    filtros: FiltrosResumo,
    *,
    por_valor: bool,
) -> list[tuple[str, float]]:
    with get_session() as session:
        ordem = (
            func.coalesce(func.sum(Devolucao.valor_nf), 0.0).desc()
            if por_valor
            else func.count(Devolucao.id).desc()
        )
        rows = (
            _query_base(session, filtros)
            .with_entities(
                Devolucao.motivo_devolucao,
                func.count(Devolucao.id).label("qtd"),
                func.coalesce(func.sum(Devolucao.valor_nf), 0.0).label("valor"),
            )
            .filter(
                Devolucao.motivo_devolucao.isnot(None),
                func.trim(Devolucao.motivo_devolucao) != "",
            )
            .group_by(Devolucao.motivo_devolucao)
            .order_by(ordem)
            .limit(5)
            .all()
        )
    if por_valor:
        return [(str(r[0]).strip(), float(r[2] or 0)) for r in rows if r[0]]
    return [(str(r[0]).strip(), float(r[1] or 0)) for r in rows if r[0]]


def top5_motivos_quantidade(filtros: FiltrosResumo) -> list[tuple[str, float]]:
    return _top5_motivos(filtros, por_valor=False)


def top5_motivos_valor(filtros: FiltrosResumo) -> list[tuple[str, float]]:
    return _top5_motivos(filtros, por_valor=True)


def _top5_clientes(
    filtros: FiltrosResumo,
    *,
    por_valor: bool,
) -> list[dict[str, Any]]:
    with get_session() as session:
        ordem = (
            func.coalesce(func.sum(Devolucao.valor_nf), 0.0).desc()
            if por_valor
            else func.count(Devolucao.id).desc()
        )
        rows = (
            _query_base(session, filtros)
            .with_entities(
                _cod_cliente_chave().label("cod"),
                func.max(Devolucao.cliente).label("nome"),
                func.count(Devolucao.id).label("qtd"),
                func.coalesce(func.sum(Devolucao.valor_nf), 0.0).label("valor"),
            )
            .group_by(_cod_cliente_chave())
            .order_by(ordem)
            .limit(5)
            .all()
        )
    resultado = []
    for cod, nome, qtd, valor in rows:
        chave = str(cod or _COD_CLIENTE_VAZIO)
        cod_exib = "" if chave == _COD_CLIENTE_VAZIO else chave
        resultado.append(
            {
                "cod_cliente": cod_exib,
                "cliente": str(nome or "").strip(),
                "quantidade": int(qtd or 0),
                "valor": float(valor or 0),
                "rotulo": _rotulo_cliente(chave, str(nome) if nome else None),
            }
        )
    return resultado


def top5_clientes_quantidade(filtros: FiltrosResumo) -> list[dict[str, Any]]:
    return _top5_clientes(filtros, por_valor=False)


def top5_clientes_valor(filtros: FiltrosResumo) -> list[dict[str, Any]]:
    return _top5_clientes(filtros, por_valor=True)


def _calcular_percentual_agregado(
    quantidade: int,
    valor_total: float,
    *,
    total_quantidade: int,
    total_valor: float,
    por_valor: bool,
) -> float:
    """Percentual conforme critério: quantidade ou valor total devolvido."""
    if por_valor:
        if total_valor <= 0:
            return 0.0
        return round(float(valor_total) / float(total_valor) * 100, 2)
    if total_quantidade <= 0:
        return 0.0
    return round(int(quantidade) / int(total_quantidade) * 100, 2)


def _agregar_com_percentual(
    filtros: FiltrosResumo,
    *,
    por_cliente: bool,
    por_valor: bool = False,
) -> list[dict[str, Any]]:
    with get_session() as session:
        base = _query_base(session, filtros)
        total_qtd = int(base.with_entities(func.count(Devolucao.id)).scalar() or 0)
        if total_qtd <= 0:
            return []

        total_valor = float(
            base.with_entities(
                func.coalesce(func.sum(Devolucao.valor_nf), 0.0)
            ).scalar()
            or 0.0
        )

        ordem = (
            func.coalesce(func.sum(Devolucao.valor_nf), 0.0).desc()
            if por_valor
            else func.count(Devolucao.id).desc()
        )

        if por_cliente:
            rows = (
                base.with_entities(
                    _cod_cliente_chave().label("cod"),
                    func.max(Devolucao.cliente).label("nome"),
                    func.count(Devolucao.id).label("qtd"),
                    func.coalesce(func.sum(Devolucao.valor_nf), 0.0).label("valor"),
                )
                .group_by(_cod_cliente_chave())
                .order_by(ordem)
                .all()
            )
            resultado = []
            for cod, nome, qtd, valor in rows:
                chave = str(cod or _COD_CLIENTE_VAZIO)
                qtd_int = int(qtd or 0)
                valor_float = float(valor or 0)
                pct = _calcular_percentual_agregado(
                    qtd_int,
                    valor_float,
                    total_quantidade=total_qtd,
                    total_valor=total_valor,
                    por_valor=por_valor,
                )
                cod_exib = "" if chave == _COD_CLIENTE_VAZIO else chave
                resultado.append(
                    {
                        "cod_cliente": cod_exib,
                        "cliente": str(nome or "").strip(),
                        "quantidade": qtd_int,
                        "valor_total": valor_float,
                        "percentual": pct,
                    }
                )
            return resultado

        rows = (
            base.with_entities(
                Devolucao.motivo_devolucao,
                func.count(Devolucao.id).label("qtd"),
                func.coalesce(func.sum(Devolucao.valor_nf), 0.0).label("valor"),
            )
            .filter(
                Devolucao.motivo_devolucao.isnot(None),
                func.trim(Devolucao.motivo_devolucao) != "",
            )
            .group_by(Devolucao.motivo_devolucao)
            .order_by(ordem)
            .all()
        )
        resultado = []
        for motivo, qtd, valor in rows:
            qtd_int = int(qtd or 0)
            valor_float = float(valor or 0)
            pct = _calcular_percentual_agregado(
                qtd_int,
                valor_float,
                total_quantidade=total_qtd,
                total_valor=total_valor,
                por_valor=por_valor,
            )
            resultado.append(
                {
                    "motivo": str(motivo or "").strip(),
                    "quantidade": qtd_int,
                    "valor_total": valor_float,
                    "percentual": pct,
                }
            )
        return resultado


def listar_agregado_tabela(
    filtros: FiltrosResumo,
    *,
    por_cliente: bool,
    por_valor: bool = False,
) -> list[dict[str, Any]]:
    """Consulta única parametrizada — agrupamento e ordenação no PostgreSQL."""
    return _agregar_com_percentual(
        filtros,
        por_cliente=por_cliente,
        por_valor=por_valor,
    )


def listar_agregado_motivos(
    filtros: FiltrosResumo,
    *,
    por_valor: bool = False,
) -> list[dict[str, Any]]:
    return listar_agregado_tabela(filtros, por_cliente=False, por_valor=por_valor)


def listar_agregado_clientes(
    filtros: FiltrosResumo,
    *,
    por_valor: bool = False,
) -> list[dict[str, Any]]:
    return listar_agregado_tabela(filtros, por_cliente=True, por_valor=por_valor)
