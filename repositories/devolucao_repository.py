"""Repositório — devoluções operacionais."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional, Union

import pandas as pd
from sqlalchemy import func, or_

from core.db import get_session
from database.models import Devolucao


def _fmt_data(valor: Optional[Union[date, datetime]]) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    return valor.strftime("%d/%m/%Y")


def _parse_data(valor: Union[str, date, datetime, None]) -> Optional[date]:
    if valor is None:
        return None
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    if isinstance(valor, datetime):
        return valor.date()
    texto = str(valor).strip()
    if not texto:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return None


def nf_ja_cadastrada(nf_nfd: str, exceto_id: Optional[int] = None) -> bool:
    chave = nf_nfd.strip()
    if not chave:
        return False
    with get_session() as session:
        q = session.query(Devolucao.id).filter(Devolucao.nf_nfd == chave)
        if exceto_id is not None:
            q = q.filter(Devolucao.id != exceto_id)
        return q.first() is not None


def obter_por_id(devolucao_id: int) -> Optional[Devolucao]:
    with get_session() as session:
        return session.get(Devolucao, devolucao_id)


def atualizar(
    devolucao_id: int,
    *,
    data_devolucao: date,
    motivo_devolucao: str,
    nf_nfd: str,
    usuario_ultima_edicao: str,
    observacao: Optional[str] = None,
    data_emissao_nf: Optional[date] = None,
    cod_cliente: Optional[str] = None,
    cliente: Optional[str] = None,
    cidade: Optional[str] = None,
    bairro: Optional[str] = None,
    vendedor: Optional[str] = None,
    valor_nf: Optional[float] = None,
) -> bool:
    with get_session() as session:
        dev = session.get(Devolucao, devolucao_id)
        if dev is None:
            return False
        dev.data_devolucao = data_devolucao
        dev.motivo_devolucao = motivo_devolucao.strip()
        dev.nf_nfd = nf_nfd.strip()
        dev.usuario_ultima_edicao = usuario_ultima_edicao.strip()
        dev.observacao = observacao
        dev.data_emissao_nf = data_emissao_nf
        dev.cod_cliente = cod_cliente
        dev.cliente = cliente
        dev.cidade = cidade
        dev.bairro = bairro
        dev.vendedor = vendedor
        dev.valor_nf = valor_nf
        dev.updated_at = datetime.utcnow()
        return True


def excluir(devolucao_id: int) -> bool:
    with get_session() as session:
        dev = session.get(Devolucao, devolucao_id)
        if dev is None:
            return False
        session.delete(dev)
        return True


def inserir(
    data_devolucao: date,
    usuario: str,
    motivo_devolucao: str,
    nf_nfd: str,
    observacao: str,
    data_emissao_nf: Optional[date] = None,
    cod_cliente: Optional[str] = None,
    cliente: Optional[str] = None,
    cidade: Optional[str] = None,
    bairro: Optional[str] = None,
    vendedor: Optional[str] = None,
    valor_nf: Optional[float] = None,
) -> int:
    with get_session() as session:
        dev = Devolucao(
            data_lancamento=data_devolucao,
            data_devolucao=data_devolucao,
            usuario=usuario,
            nf_nfd=nf_nfd.strip(),
            motivo_devolucao=motivo_devolucao,
            observacao=observacao,
            data_emissao_nf=data_emissao_nf,
            cod_cliente=cod_cliente,
            cliente=cliente,
            cidade=cidade,
            bairro=bairro,
            vendedor=vendedor,
            valor_nf=valor_nf,
        )
        session.add(dev)
        session.flush()
        return dev.id


def listar(
    busca: str = "",
    *,
    limit: int = 500,
    offset: int = 0,
) -> list[Devolucao]:
    with get_session() as session:
        q = session.query(Devolucao).order_by(
            Devolucao.data_devolucao.desc(), Devolucao.id.desc()
        )
        if busca:
            termo = f"%{busca.strip()}%"
            q = q.filter(
                or_(
                    Devolucao.usuario.ilike(termo),
                    Devolucao.nf_nfd.ilike(termo),
                    Devolucao.motivo_devolucao.ilike(termo),
                    Devolucao.observacao.ilike(termo),
                    Devolucao.cliente.ilike(termo),
                    Devolucao.cod_cliente.ilike(termo),
                    Devolucao.vendedor.ilike(termo),
                    Devolucao.cidade.ilike(termo),
                    Devolucao.bairro.ilike(termo),
                )
            )
        if offset > 0:
            q = q.offset(offset)
        return q.limit(limit).all()


def contar(busca: str = "") -> int:
    with get_session() as session:
        q = session.query(Devolucao)
        if busca:
            termo = f"%{busca.strip()}%"
            q = q.filter(
                or_(
                    Devolucao.usuario.ilike(termo),
                    Devolucao.nf_nfd.ilike(termo),
                    Devolucao.motivo_devolucao.ilike(termo),
                    Devolucao.cod_cliente.ilike(termo),
                    Devolucao.vendedor.ilike(termo),
                )
            )
        return q.count()


def contar_total() -> int:
    with get_session() as session:
        return session.query(Devolucao).count()


def obter_metricas_operacionais() -> dict[str, Any]:
    """Agregações para cards do dashboard — uma sessão, queries leves."""
    with get_session() as session:
        soma_valor = session.query(
            func.coalesce(func.sum(Devolucao.valor_nf), 0.0)
        ).scalar()
        total = session.query(func.count(Devolucao.id)).scalar() or 0
        ultima = session.query(func.max(Devolucao.created_at)).scalar()

        motivo_row = (
            session.query(
                Devolucao.motivo_devolucao,
                func.count(Devolucao.id).label("total"),
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
        "ultima_atualizacao": ultima,
    }


def para_dataframe(rows: list[Devolucao]) -> pd.DataFrame:
    colunas = ["data_devolucao", "nf_nfd", "motivo_devolucao", "observacao", "usuario"]
    if not rows:
        return pd.DataFrame(columns=colunas)

    dados = [
        {
            "data_devolucao": _fmt_data(r.data_devolucao),
            "nf_nfd": r.nf_nfd or "—",
            "motivo_devolucao": r.motivo_devolucao,
            "observacao": r.observacao or "—",
            "usuario": r.usuario,
        }
        for r in rows
    ]
    return pd.DataFrame(dados)
