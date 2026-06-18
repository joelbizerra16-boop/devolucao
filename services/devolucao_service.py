"""Serviço de devoluções — orquestra validação, SAP e persistência."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional, Union

import pandas as pd
import streamlit as st

from core.cache_read import TTL_DEVOLUCOES, limpar_cache_leitura
from core.constants import TRATATIVA_PADRAO
from core.auth import get_current_user
from core.permissions import pode_editar_tratativa
from core.system_log import log_event
from repositories import devolucao_repository
from services import sap_service
from services.validation_service import validar_cadastro_devolucao, validar_edicao_devolucao


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


def buscar_dados_sap(nf_nfd: str) -> tuple[bool, str, Optional[dict[str, Any]]]:
    return sap_service.buscar_nf_cache(nf_nfd)


def cadastrar_devolucao(
    data_devolucao: Union[date, datetime],
    nf_nfd: str,
    motivo_devolucao: str,
    observacao: str,
    usuario: str,
) -> tuple[bool, str, Optional[int]]:
    try:
        dd = _parse_data(data_devolucao)
        nf = str(nf_nfd or "").strip()

        ok_sap, msg_sap, sap = sap_service.obter_por_nf(nf)

        validacao = validar_cadastro_devolucao(
            data_devolucao=dd,
            nf_nfd=nf,
            motivo_devolucao=motivo_devolucao,
            observacao=observacao,
            usuario=usuario,
            sap_encontrado=ok_sap,
            nf_duplicada=devolucao_repository.nf_ja_cadastrada(nf),
            dados_sap_validos=bool(sap and sap.get("nf_nfd")),
        )
        if not validacao.ok:
            return False, validacao.message, None

        log_event(
            "persist",
            f"cadastrar_devolucao nf={nf} data={dd} usuario={usuario!r}",
        )
        dev_id = devolucao_repository.inserir(
            data_devolucao=dd,
            usuario=str(usuario).strip(),
            motivo_devolucao=str(motivo_devolucao).strip(),
            nf_nfd=nf,
            observacao=str(observacao or "").strip() or None,
            data_emissao_nf=sap.get("data_emissao_nf") if sap else None,
            cod_cliente=sap.get("cod_cliente") if sap else None,
            cliente=sap.get("cliente") if sap else None,
            cidade=sap.get("cidade") if sap else None,
            bairro=sap.get("bairro") if sap else None,
            vendedor=sap.get("vendedor") if sap else None,
            valor_nf=sap.get("valor_nf") if sap else None,
        )
        limpar_cache_leitura()
        log_event("persist", f"cadastrar_devolucao OK id={dev_id} cache_limpo=True")
        return True, "Devolução salva com sucesso.", dev_id
    except Exception as exc:
        log_event("persist", f"cadastrar_devolucao ERRO nf={str(nf_nfd or '').strip()!r}: {exc}", exc)
        return False, f"Erro ao salvar devolução: {exc}", None


def _formatar_data(valor: Any) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, datetime):
        return valor.date().strftime("%d/%m/%Y")
    texto = str(valor).strip()
    if not texto or texto in ("—", "NaT", "nan"):
        return "—"
    try:
        return pd.to_datetime(valor, dayfirst=True).strftime("%d/%m/%Y")
    except Exception:
        return texto


def _formatar_valor_br(valor: Any) -> str:
    if valor is None:
        return "—"
    try:
        if pd.isna(valor):
            return "—"
    except TypeError:
        pass
    try:
        num = float(valor)
        texto = f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {texto}"
    except (TypeError, ValueError):
        return "—"


def _texto_celula(valor: Any) -> str:
    if valor is None:
        return "—"
    texto = str(valor).strip()
    return texto if texto and texto.lower() not in ("nan", "none", "null") else "—"


def _valor_linha(row: Any, campo: str) -> Any:
    if isinstance(row, dict):
        return row.get(campo)
    return getattr(row, campo, None)


def _serializar_listview_operacional(row: Any) -> dict[str, Any]:
    data_dev = _valor_linha(row, "data_devolucao")
    if isinstance(data_dev, datetime):
        data_dev = data_dev.isoformat()
    elif isinstance(data_dev, date):
        data_dev = data_dev.isoformat()

    data_emissao = _valor_linha(row, "data_emissao_nf")
    if isinstance(data_emissao, datetime):
        data_emissao = data_emissao.isoformat()
    elif isinstance(data_emissao, date):
        data_emissao = data_emissao.isoformat()

    return {
        "data_devolucao": data_dev,
        "data_emissao_nf": data_emissao,
        "usuario": _valor_linha(row, "usuario"),
        "usuario_ultima_edicao": _valor_linha(row, "usuario_ultima_edicao"),
        "nf_nfd": _valor_linha(row, "nf_nfd"),
        "cod_cliente": _valor_linha(row, "cod_cliente"),
        "vendedor": _valor_linha(row, "vendedor"),
        "valor_nf": _valor_linha(row, "valor_nf"),
        "cidade": _valor_linha(row, "cidade"),
        "bairro": _valor_linha(row, "bairro"),
        "motivo_devolucao": _valor_linha(row, "motivo_devolucao"),
        "tratativa": _valor_linha(row, "tratativa"),
    }


def preparar_listview_operacional(rows: list) -> pd.DataFrame:
    """Monta DataFrame da list view operacional (padrão ERP/WMS)."""
    colunas = [
        "RESPONSAVEL / DEVOLUÇÃO",
        "D. EMISSÃO",
        "NF/NFD",
        "COD CLIENTE",
        "VENDEDOR",
        "VALOR",
        "CIDADE",
        "BAIRRO",
        "MOTIVO DEVOLUÇÃO",
    ]
    if not rows:
        return pd.DataFrame(columns=colunas)

    linhas = []
    for r in rows:
        usuario = _nome_responsavel_exibicao(r)
        data_dev = _formatar_data(_valor_linha(r, "data_devolucao"))
        linhas.append(
            {
                "RESPONSAVEL / DEVOLUÇÃO": f"{usuario}\n{data_dev}",
                "D. EMISSÃO": _formatar_data(_valor_linha(r, "data_emissao_nf")),
                "NF/NFD": _texto_celula(_valor_linha(r, "nf_nfd")),
                "COD CLIENTE": _texto_celula(_valor_linha(r, "cod_cliente")),
                "VENDEDOR": _texto_celula(_valor_linha(r, "vendedor")),
                "VALOR": _formatar_valor_br(_valor_linha(r, "valor_nf")),
                "CIDADE": _texto_celula(_valor_linha(r, "cidade")),
                "BAIRRO": _texto_celula(_valor_linha(r, "bairro")),
                "MOTIVO DEVOLUÇÃO": _texto_celula(_valor_linha(r, "motivo_devolucao")),
            }
        )

    return pd.DataFrame(linhas, columns=colunas)


@st.cache_data(ttl=TTL_DEVOLUCOES, show_spinner=False)
def listar_devolucoes_cache(busca: str = "") -> tuple[dict[str, Any], ...]:
    from core.search_utils import normalizar_texto_busca

    rows = devolucao_repository.listar(busca=normalizar_texto_busca(busca or ""))
    return tuple(_serializar_listview_operacional(r) for r in rows)


def listar_devolucoes(busca: str = "") -> pd.DataFrame:
    return preparar_listview_operacional(listar_devolucoes_cache(busca or ""))


def _rotulo_qtd_devolucoes(qtd: int) -> str:
    n = int(qtd or 0)
    return f"{n} devolução" if n == 1 else f"{n} devoluções"


@st.cache_data(ttl=TTL_DEVOLUCOES, show_spinner=False)
def obter_metricas_cards_cache() -> dict[str, str]:
    raw = devolucao_repository.obter_metricas_operacionais()

    motivo = raw.get("principal_motivo")
    motivo_qtd = int(raw.get("principal_motivo_qtd") or 0)
    if motivo:
        principal = motivo
        principal_sub = _rotulo_qtd_devolucoes(motivo_qtd)
    else:
        principal = "N/A"
        principal_sub = ""

    return {
        "impacto_financeiro": _formatar_valor_br(raw.get("soma_valor_nf", 0)),
        "devolucoes": str(int(raw.get("total_devolucoes") or 0)),
        "principal_motivo": principal,
        "principal_motivo_sub": principal_sub,
    }


def _formatar_data_hora(valor: Any) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "—"


def obter_metricas_cards() -> dict[str, str]:
    """Indicadores operacionais reais para os cards da consulta."""
    return obter_metricas_cards_cache()


def contar_para_cards() -> dict[str, str]:
    """Compatibilidade — preferir obter_metricas_cards()."""
    return obter_metricas_cards()


def _nome_responsavel_exibicao(row: Any) -> str:
    """Último responsável visível — quem editou por último, senão quem cadastrou."""
    editado = _texto_celula(_valor_linha(row, "usuario_ultima_edicao"))
    if editado != "—":
        return editado
    return _texto_celula(_valor_linha(row, "usuario"))


def atualizar_devolucao(
    devolucao_id: int,
    data_devolucao: Union[date, datetime],
    nf_nfd: str,
    motivo_devolucao: str,
    editor: str,
) -> tuple[bool, str]:
    try:
        dd = _parse_data(data_devolucao)
        nf = str(nf_nfd or "").strip()
        editor_nome = str(editor or "").strip()

        ok_sap, _, sap = sap_service.obter_por_nf(nf)
        validacao = validar_edicao_devolucao(
            data_devolucao=dd,
            nf_nfd=nf,
            motivo_devolucao=motivo_devolucao,
            editor=editor_nome,
            sap_encontrado=ok_sap,
            nf_duplicada=devolucao_repository.nf_ja_cadastrada(nf, exceto_id=devolucao_id),
            dados_sap_validos=bool(sap and sap.get("nf_nfd")),
        )
        if not validacao.ok:
            return False, validacao.message

        ok = devolucao_repository.atualizar(
            devolucao_id,
            data_devolucao=dd,
            motivo_devolucao=str(motivo_devolucao).strip(),
            nf_nfd=nf,
            usuario_ultima_edicao=editor_nome,
            data_emissao_nf=sap.get("data_emissao_nf") if sap else None,
            cod_cliente=sap.get("cod_cliente") if sap else None,
            cliente=sap.get("cliente") if sap else None,
            cidade=sap.get("cidade") if sap else None,
            bairro=sap.get("bairro") if sap else None,
            vendedor=sap.get("vendedor") if sap else None,
            valor_nf=sap.get("valor_nf") if sap else None,
        )
        if not ok:
            return False, "Devolução não encontrada."
        limpar_cache_leitura()
        return True, "Devolução atualizada com sucesso."
    except Exception as exc:
        return False, f"Erro ao atualizar devolução: {exc}"


def excluir_devolucao(devolucao_id: int) -> tuple[bool, str]:
    try:
        ok = devolucao_repository.excluir(devolucao_id)
        if not ok:
            return False, "Devolução não encontrada."
        limpar_cache_leitura()
        return True, "Devolução excluída com sucesso."
    except Exception as exc:
        return False, f"Erro ao excluir devolução: {exc}"


def _texto_tratativa_exibicao(valor: Any) -> str:
    texto = _texto_celula(valor)
    return texto if texto != "—" else TRATATIVA_PADRAO


def atualizar_tratativa(devolucao_id: int, tratativa: str) -> tuple[bool, str]:
    if not pode_editar_tratativa():
        return False, "Permissão negada. Apenas o perfil VISITANTE pode editar a tratativa."
    texto = str(tratativa or "").strip() or TRATATIVA_PADRAO
    if len(texto) > 255:
        return False, "Tratativa deve ter no máximo 255 caracteres."
    user = get_current_user()
    usuario = user.nome if user else ""
    try:
        ok = devolucao_repository.atualizar_tratativa(devolucao_id, texto, usuario)
        if not ok:
            return False, "Devolução não encontrada."
        limpar_cache_leitura()
        return True, "Tratativa atualizada com sucesso."
    except Exception as exc:
        return False, f"Erro ao atualizar tratativa: {exc}"
