"""Repositório — motivos de devolução (PostgreSQL / Supabase)."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from sqlalchemy import func

from core.db import get_session, get_write_session
from database.models import Motivo


def listar_ativos() -> list[Motivo]:
    with get_session() as session:
        return (
            session.query(Motivo)
            .filter(Motivo.ativo.is_(True))
            .order_by(Motivo.descricao.asc())
            .all()
        )


def listar_descricoes_ativos() -> list[str]:
    with get_session() as session:
        rows = (
            session.query(Motivo.descricao)
            .filter(Motivo.ativo.is_(True))
            .order_by(Motivo.descricao.asc())
            .all()
        )
    return [str(r[0]) for r in rows if r[0] is not None]


def listar_todos() -> list[Motivo]:
    with get_session() as session:
        return session.query(Motivo).order_by(Motivo.descricao.asc()).all()


def listar_df() -> pd.DataFrame:
    with get_session() as session:
        rows = (
            session.query(Motivo.id, Motivo.descricao, Motivo.ativo)
            .order_by(Motivo.descricao.asc())
            .all()
        )
    if not rows:
        return pd.DataFrame(columns=["id", "descricao", "ativo"])
    return pd.DataFrame(
        [{"id": r[0], "descricao": r[1], "ativo": r[2]} for r in rows]
    )


def buscar_por_descricao(descricao: str) -> Optional[Motivo]:
    chave = descricao.strip().lower()
    if not chave:
        return None
    with get_session() as session:
        return (
            session.query(Motivo)
            .filter(func.lower(Motivo.descricao) == chave)
            .first()
        )


def inserir(descricao: str) -> int:
    with get_write_session() as session:
        motivo = Motivo(descricao=descricao.strip(), ativo=True)
        session.add(motivo)
        session.flush()
        return motivo.id


def excluir_por_descricao(descricao: str) -> bool:
    with get_write_session() as session:
        motivo = (
            session.query(Motivo)
            .filter(func.lower(Motivo.descricao) == descricao.strip().lower())
            .first()
        )
        if motivo is None:
            return False
        session.delete(motivo)
        return True


def importar_descricoes(descricoes: list[str]) -> int:
    inseridos = 0
    with get_write_session() as session:
        existentes = {
            (r[0] or "").strip().lower()
            for r in session.query(Motivo.descricao).all()
        }
        for texto in descricoes:
            chave = texto.strip().lower()
            if not chave or chave in existentes:
                continue
            session.add(Motivo(descricao=texto.strip(), ativo=True))
            existentes.add(chave)
            inseridos += 1
    return inseridos
