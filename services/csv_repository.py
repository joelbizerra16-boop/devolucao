"""
Persistência em CSV — camada desacoplada, pronta para migração a banco.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Optional, Union

import pandas as pd

from core.paths import (
    DEVOLUCOES_COLUNAS,
    DEVOLUCOES_CSV,
    MOTIVOS_COLUNAS,
    MOTIVOS_CSV,
    MOTIVOS_PADRAO,
    DATA_DIR,
    UPLOADS_SAP_DIR,
)


def init_csv_storage() -> None:
    """Garante pastas de upload; motivos e devoluções ficam no banco (Supabase)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_SAP_DIR.mkdir(parents=True, exist_ok=True)


def _ler_csv(caminho: Path, colunas: list[str]) -> pd.DataFrame:
    if not caminho.exists():
        return pd.DataFrame(columns=colunas)
    df = pd.read_csv(caminho, encoding="utf-8-sig")
    for col in colunas:
        if col not in df.columns:
            df[col] = ""
    return df[colunas]


def _salvar_csv(caminho: Path, df: pd.DataFrame) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, encoding="utf-8-sig")


# --- Motivos ---


def listar_motivos() -> list[str]:
    from services.motivo_service import listar_motivos as _listar

    return _listar()


def adicionar_motivo(descricao: str) -> tuple[bool, str]:
    from repositories import motivo_repository

    descricao = descricao.strip()
    if not descricao:
        return False, "Informe a descrição do motivo."
    if motivo_repository.buscar_por_descricao(descricao):
        return False, "Este motivo já está cadastrado."
    try:
        motivo_repository.inserir(descricao)
        from core.cache_read import limpar_cache_leitura

        limpar_cache_leitura()
        return True, f"Motivo «{descricao}» adicionado."
    except Exception as exc:
        return False, f"Erro ao salvar motivo: {exc}"


def excluir_motivo(descricao: str) -> tuple[bool, str]:
    from repositories import motivo_repository

    descricao = descricao.strip()
    if not descricao:
        return False, "Selecione um motivo para excluir."
    try:
        if not motivo_repository.excluir_por_descricao(descricao):
            return False, "Motivo não encontrado."
        from core.cache_read import limpar_cache_leitura

        limpar_cache_leitura()
        return True, f"Motivo «{descricao}» excluído."
    except Exception as exc:
        return False, f"Erro ao excluir motivo: {exc}"


def listar_motivos_df() -> pd.DataFrame:
    from services.motivo_service import listar_motivos_df as _listar_df

    return _listar_df()


def ler_planilha_motivos_upload(arquivo) -> pd.DataFrame:
    """Lê planilha de motivos enviada via file_uploader (CSV ou XLSX)."""
    nome = arquivo.name.lower()
    if nome.endswith(".csv"):
        return pd.read_csv(arquivo, encoding="utf-8-sig")
    return pd.read_excel(arquivo)


def importar_motivos_planilha(df: pd.DataFrame) -> tuple[bool, str]:
    """
    Importa motivos da coluna 'motivo'.
    Acrescenta apenas novos (não sobrescreve existentes).
    """
    col_motivo = None
    for col in df.columns:
        if str(col).strip().lower() == "motivo":
            col_motivo = col
            break
    if col_motivo is None:
        return False, 'A planilha deve conter a coluna "motivo".'

    candidatos = df[col_motivo].dropna().astype(str).str.strip()
    candidatos = candidatos[candidatos != ""].unique()
    if len(candidatos) == 0:
        return False, "Nenhum motivo válido encontrado na planilha."

    from repositories import motivo_repository

    novos = [str(t).strip() for t in candidatos if str(t).strip()]
    try:
        inseridos = motivo_repository.importar_descricoes(novos)
        if inseridos == 0:
            return True, "Nenhum motivo novo para importar."
        from core.cache_read import limpar_cache_leitura

        limpar_cache_leitura()
        return True, f"{inseridos} motivo(s) importado(s) com sucesso."
    except Exception as exc:
        return False, f"Erro ao importar motivos: {exc}"


# --- Devoluções (CSV) ---


def _formatar_data_devolucao(valor: Union[str, date, datetime]) -> str:
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    return str(valor).strip()


def salvar_devolucao_csv(
    d_devolucao: Union[str, date, datetime],
    nf: str,
    motivo: str,
    observacao: str,
    responsavel: str,
) -> tuple[bool, str]:
    d_devolucao = _formatar_data_devolucao(d_devolucao)
    if not d_devolucao:
        return False, "Informe a data da devolução."
    if not motivo:
        return False, "Selecione um motivo."

    nf_limpo = nf.strip()
    df = _ler_csv(DEVOLUCOES_CSV, DEVOLUCOES_COLUNAS)
    if not df.empty:
        duplicado = df["d_devolucao"].astype(str).str.strip().eq(d_devolucao)
        if nf_limpo:
            duplicado &= df["nf"].astype(str).str.strip().eq(nf_limpo)
        if duplicado.any():
            ref = f"{d_devolucao} / NF {nf_limpo}" if nf_limpo else d_devolucao
            return False, f"Já existe registro para «{ref}»."

    registro = {
        "d_devolucao": d_devolucao,
        "nf": nf_limpo,
        "motivo": motivo.strip(),
        "observacao": observacao.strip(),
        "responsavel": responsavel.strip(),
        "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
    _salvar_csv(DEVOLUCOES_CSV, df)
    return True, f"Devolução de {d_devolucao} salva com sucesso."


def listar_devolucoes_csv() -> pd.DataFrame:
    return _ler_csv(DEVOLUCOES_CSV, DEVOLUCOES_COLUNAS)


# --- Upload SAP ---


def salvar_arquivo_sap(nome_arquivo: str, conteudo: bytes) -> Path:
    UPLOADS_SAP_DIR.mkdir(parents=True, exist_ok=True)
    destino = UPLOADS_SAP_DIR / nome_arquivo
    destino.write_bytes(conteudo)
    return destino


def ler_planilha(caminho: Path) -> pd.DataFrame:
    sufixo = caminho.suffix.lower()
    if sufixo == ".csv":
        return pd.read_csv(caminho, encoding="utf-8-sig")
    if sufixo in (".xlsx", ".xls"):
        return pd.read_excel(caminho)
    raise ValueError("Formato não suportado. Use CSV ou XLSX.")
