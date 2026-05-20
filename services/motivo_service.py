"""Serviço de motivos — delega ao repositório PostgreSQL com cache de leitura."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.cache_read import TTL_MOTIVOS, limpar_cache_leitura
from repositories import motivo_repository


@st.cache_data(ttl=TTL_MOTIVOS, show_spinner=False)
def listar_motivos_cache() -> tuple[str, ...]:
    return tuple(motivo_repository.listar_descricoes_ativos())


def listar_motivos() -> list[str]:
    return list(listar_motivos_cache())


@st.cache_data(ttl=TTL_MOTIVOS, show_spinner=False)
def listar_motivos_df_cache() -> pd.DataFrame:
    return motivo_repository.listar_df()


def listar_motivos_df() -> pd.DataFrame:
    return listar_motivos_df_cache()


def adicionar_motivo(descricao: str) -> tuple[bool, str]:
    from services.csv_repository import adicionar_motivo as _add

    ok, msg = _add(descricao)
    if ok:
        limpar_cache_leitura()
    return ok, msg


def excluir_motivo(descricao: str) -> tuple[bool, str]:
    from services.csv_repository import excluir_motivo as _del

    ok, msg = _del(descricao)
    if ok:
        limpar_cache_leitura()
    return ok, msg
