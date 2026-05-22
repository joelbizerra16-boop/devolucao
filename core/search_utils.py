"""Busca textual enterprise — normalização, tokens e filtros SQLAlchemy."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from sqlalchemy import String, and_, cast, func, or_
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

from database.models import Devolucao

_SUBSTITUICOES_ACENTO = (
    ("á", "a"),
    ("à", "a"),
    ("ã", "a"),
    ("â", "a"),
    ("ä", "a"),
    ("é", "e"),
    ("è", "e"),
    ("ê", "e"),
    ("ë", "e"),
    ("í", "i"),
    ("ì", "i"),
    ("î", "i"),
    ("ï", "i"),
    ("ó", "o"),
    ("ò", "o"),
    ("õ", "o"),
    ("ô", "o"),
    ("ö", "o"),
    ("ú", "u"),
    ("ù", "u"),
    ("û", "u"),
    ("ü", "u"),
    ("ç", "c"),
    ("ñ", "n"),
)

# Campos pesquisáveis na listagem operacional (alinhado ao que o usuário vê/copia)
CAMPOS_BUSCA_DEVOLUCAO: tuple[InstrumentedAttribute[Any], ...] = (
    Devolucao.usuario,
    Devolucao.usuario_ultima_edicao,
    Devolucao.nf_nfd,
    Devolucao.motivo_devolucao,
    Devolucao.cod_cliente,
    Devolucao.vendedor,
    Devolucao.cliente,
    Devolucao.observacao,
    Devolucao.cidade,
    Devolucao.bairro,
)


_ESPACOS_UNICODE = re.compile(
    r"[\s\u00a0\u1680\u2000-\u200b\u202f\u205f\u3000\ufeff]+"
)


def normalizar_texto_busca(texto: str) -> str:
    """Lower, sem acentos combinantes, espaços colapsados (inclui NBSP do copy/paste)."""
    if not texto:
        return ""
    t = str(texto).strip()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.lower()
    t = _ESPACOS_UNICODE.sub(" ", t)
    t = re.sub(r" +", " ", t)
    return t.strip()


def _escape_like(token: str) -> str:
    return token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _coluna_normalizada(col: InstrumentedAttribute[Any]) -> ColumnElement[Any]:
    """lower + sem acentos + coalesce + NBSP→espaço + colapsa espaços."""
    expr = func.coalesce(cast(col, String), "")
    expr = func.lower(expr)
    for de, para in _SUBSTITUICOES_ACENTO:
        expr = func.replace(expr, de, para)
    # Dados SAP/importação costumam usar espaço não separável entre palavras do vendedor
    expr = func.replace(expr, "\u00a0", " ")
    expr = func.replace(expr, chr(0xA0), " ")
    expr = func.regexp_replace(expr, r"[\s\u00a0]+", " ", "g")
    return func.trim(expr, " ")


def filtro_busca_devolucao(busca: str) -> ColumnElement[bool] | None:
    """
    Filtro AND por token: cada palavra deve aparecer em pelo menos um campo.
    Case insensitive; tolera acentos (busca sem acento encontra texto acentuado se
    o texto no banco também passar por lower — para match forte use tokens parciais).
    """
    norm = normalizar_texto_busca(busca)
    if not norm:
        return None

    tokens = [_escape_like(t) for t in norm.split() if len(t) >= 1]
    if not tokens:
        return None

    clausulas_token: list[ColumnElement[bool]] = []
    for token in tokens:
        padrao = f"%{token}%"
        match_campo = or_(
            *[
                _coluna_normalizada(campo).like(padrao, escape="\\")
                for campo in CAMPOS_BUSCA_DEVOLUCAO
            ]
        )
        clausulas_token.append(match_campo)

    # Frase inteira (copy/paste exato) — reforço para nome completo do vendedor
    frase = _escape_like(norm)
    if " " in frase and len(frase) >= 3:
        padrao_frase = f"%{frase}%"
        match_frase = or_(
            *[
                _coluna_normalizada(campo).like(padrao_frase, escape="\\")
                for campo in CAMPOS_BUSCA_DEVOLUCAO
            ]
        )
        return or_(and_(*clausulas_token), match_frase)

    return and_(*clausulas_token)


def aplicar_busca_query(query: Any, busca: str) -> Any:
    """Aplica filtro de busca em query SQLAlchemy de Devolucao."""
    filtro = filtro_busca_devolucao(busca)
    if filtro is not None:
        return query.filter(filtro)
    return query
