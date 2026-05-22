"""Repositório — devoluções operacionais."""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
from typing import Any, Optional, Union

import pandas as pd
from sqlalchemy import func

from core.db import get_session, get_write_session, is_postgres
from core.search_utils import aplicar_busca_query
from core.orm_serialize import devolucao_para_dict, parse_iso_date
from core.system_log import log_event
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


def _dict_para_devolucao_ns(d: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(
        id=d["id"],
        data_devolucao=parse_iso_date(d["data_devolucao"]),
        usuario=d.get("usuario"),
        usuario_ultima_edicao=d.get("usuario_ultima_edicao"),
        motivo_devolucao=d.get("motivo_devolucao"),
        nf_nfd=d.get("nf_nfd"),
        valor_nf=d.get("valor_nf"),
        cod_cliente=d.get("cod_cliente"),
        cliente=d.get("cliente"),
        cidade=d.get("cidade"),
        bairro=d.get("bairro"),
        vendedor=d.get("vendedor"),
        observacao=d.get("observacao"),
        data_emissao_nf=parse_iso_date(d.get("data_emissao_nf")),
    )


def obter_por_id(devolucao_id: int) -> Optional[SimpleNamespace]:
    """Namespace leve — nunca retorna entidade ORM (evita DetachedInstanceError)."""
    with get_session() as session:
        dev = session.get(Devolucao, devolucao_id)
        if dev is None:
            return None
        return _dict_para_devolucao_ns(devolucao_para_dict(dev))


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
    with get_write_session() as session:
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
    with get_write_session() as session:
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
    nf = nf_nfd.strip()
    backend = "PostgreSQL" if is_postgres() else "SQLite"
    log_event(
        "persist",
        f"INSERT devolucao iniciado backend={backend} nf={nf} data={data_devolucao}",
    )
    with get_write_session() as session:
        dev = Devolucao(
            data_lancamento=data_devolucao,
            data_devolucao=data_devolucao,
            usuario=usuario,
            nf_nfd=nf,
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
        dev_id = int(dev.id)
        if session.get(Devolucao, dev_id) is None:
            raise RuntimeError("flush() não materializou o registro na sessão")

    if not confirmar_persistencia(dev_id, nf):
        log_event("persist", f"FALHA pós-commit: id={dev_id} nf={nf} não encontrado")
        raise RuntimeError("Registro não confirmado no banco após commit")

    log_event("persist", f"INSERT devolucao OK id={dev_id} nf={nf}")
    return dev_id


def confirmar_persistencia(devolucao_id: int, nf_nfd: str) -> bool:
    """SELECT imediato após commit — evita falso positivo de sucesso."""
    chave = nf_nfd.strip()
    with get_session() as session:
        row = (
            session.query(Devolucao.id)
            .filter(Devolucao.id == devolucao_id, Devolucao.nf_nfd == chave)
            .first()
        )
        return row is not None


def listar(
    busca: str = "",
    *,
    limit: int = 500,
    offset: int = 0,
) -> list[dict[str, Any]]:
    with get_session() as session:
        q = session.query(Devolucao).order_by(
            Devolucao.data_devolucao.desc(), Devolucao.id.desc()
        )
        q = aplicar_busca_query(q, busca)
        if offset > 0:
            q = q.offset(offset)
        rows = q.limit(limit).all()
        return [devolucao_para_dict(r) for r in rows]


def contar(busca: str = "") -> int:
    with get_session() as session:
        q = session.query(Devolucao)
        q = aplicar_busca_query(q, busca)
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
