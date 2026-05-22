"""Serviço de importação e consulta de dados SAP — substituição total da base."""

from __future__ import annotations

import io
import re
import shutil
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import streamlit as st

from core.cache_read import TTL_SAP, limpar_cache_leitura
from core.paths import UPLOADS_SAP_DIR
from core.sap_import_log import log_import_sap
from repositories import sap_repository

EXTENSOES_VALIDAS = {".csv", ".xlsx", ".xls"}

# Cabeçalhos REAIS da planilha SAP → campos internos do banco
COLUMN_MAPPING: dict[str, str] = {
    # Export SAP clássico
    "NF": "nf_nfd",
    "NF/NFD": "nf_nfd",
    "Código do cliente/fornecedor": "cod_cliente",
    "Código do cliente/forn": "cod_cliente",
    "COD CLIENTE": "cod_cliente",
    "Cliente": "cliente",
    "Cidade": "cidade",
    "CIDADE": "cidade",
    "Bairro": "bairro",
    "BAIRRO": "bairro",
    "Vendedor": "vendedor",
    "VENDEDOR": "vendedor",
    "ValorNF": "valor_nf",
    "VALOR NF": "valor_nf",
    "DataNF": "data_emissao_nf",
    "D. EMISSÃO-NF": "data_emissao_nf",
    "D. EMISSAO-NF": "data_emissao_nf",
}

# Nome amigável na planilha (mensagens de erro)
LABEL_PLANILHA_POR_CAMPO: dict[str, str] = {
    "nf_nfd": "NF ou NF/NFD",
    "cod_cliente": "COD CLIENTE ou Código do cliente/fornecedor",
    "cliente": "Cliente",
    "cidade": "Cidade",
    "bairro": "Bairro",
    "vendedor": "Vendedor",
    "valor_nf": "ValorNF ou VALOR NF",
    "data_emissao_nf": "DataNF ou D. EMISSÃO-NF",
}

# Aliases adicionais (após normalização de headers)
ALIASES_HEADERS: dict[str, str] = {
    "nf": "nf_nfd",
    "nf nfd": "nf_nfd",
    "nota fiscal": "nf_nfd",
    "codigo do cliente/fornecedor": "cod_cliente",
    "codigo do cliente fornecedor": "cod_cliente",
    "codigo do cliente/forn": "cod_cliente",
    "cod cliente": "cod_cliente",
    "codigo cliente": "cod_cliente",
    "valornf": "valor_nf",
    "valor nf": "valor_nf",
    "datanf": "data_emissao_nf",
    "data nf": "data_emissao_nf",
    "d emissao nf": "data_emissao_nf",
    "d. emissao nf": "data_emissao_nf",
    "emissao nf": "data_emissao_nf",
}

COLUNAS_OBRIGATORIAS = (
    "nf_nfd",
    "cod_cliente",
    "cliente",
    "cidade",
    "bairro",
    "vendedor",
    "valor_nf",
    "data_emissao_nf",
)

MSG_SUCESSO = "Base SAP importada com sucesso."
MSG_ERRO = "Falha ao importar dados SAP."


def _normalizar_header(col: str) -> str:
    """Remove espaços, acentos e padroniza para comparação."""
    texto = str(col).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace("/", " ").replace("\\", " ")
    texto = re.sub(r"\s+", " ", texto).strip().lower()
    return texto


def _detectar_por_conteudo(col_norm: str) -> Optional[str]:
    """Fallback: reconhece coluna SAP pelo texto do cabeçalho."""
    if col_norm in ("nf", "n f", "nota fiscal", "numero nf", "nf nfd"):
        return "nf_nfd"
    if "nf" in col_norm and "nfd" in col_norm:
        return "nf_nfd"
    if ("codigo" in col_norm or col_norm.startswith("cod ")) and "cliente" in col_norm:
        return "cod_cliente"
    if col_norm in ("cod cliente", "codigo cliente"):
        return "cod_cliente"
    if col_norm == "cliente" or (col_norm.startswith("cliente") and "cod" not in col_norm):
        return "cliente"
    if col_norm == "cidade":
        return "cidade"
    if col_norm == "bairro":
        return "bairro"
    if col_norm == "vendedor":
        return "vendedor"
    if "valor" in col_norm and "nf" in col_norm:
        return "valor_nf"
    if "emissao" in col_norm and "nf" in col_norm:
        return "data_emissao_nf"
    if "datanf" in col_norm.replace(" ", "") or col_norm == "data nf":
        return "data_emissao_nf"
    return None


def _mapa_headers() -> dict[str, str]:
    """Mapa header normalizado → coluna interna do banco."""
    mapa: dict[str, str] = {}
    for origem, destino in COLUMN_MAPPING.items():
        mapa[_normalizar_header(origem)] = destino
    for origem, destino in ALIASES_HEADERS.items():
        mapa[_normalizar_header(origem)] = destino
    return mapa


def _mapear_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    mapa = _mapa_headers()
    rename: dict[str, str] = {}
    for col in df.columns:
        norm = _normalizar_header(col)
        destino = mapa.get(norm) or _detectar_por_conteudo(norm)
        if destino and destino not in rename.values():
            rename[col] = destino

    df = df.rename(columns=rename)

    if "cliente" not in df.columns and "cod_cliente" in df.columns:
        df["cliente"] = df["cod_cliente"]

    faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltantes:
        labels = [LABEL_PLANILHA_POR_CAMPO.get(c, c) for c in faltantes]
        raise ValueError(
            "Colunas obrigatórias ausentes na planilha SAP: "
            + ", ".join(labels)
            + ". Verifique os cabeçalhos do arquivo exportado."
        )

    return df[list(COLUNAS_OBRIGATORIAS)]


def _sanitizar_texto(valor: Any, upper: bool = False) -> Optional[str]:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    if not texto or texto.lower() in ("nan", "none", "null"):
        return None
    if texto.upper() in ("N/C", "NC", "N\\C", "-"):
        return "N/C"
    return texto.upper() if upper else texto


def _sanitizar_nf(valor: Any) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    if isinstance(valor, float) and valor == int(valor):
        return str(int(valor)).strip()
    texto = str(valor).strip()
    if texto.endswith(".0") and texto[:-2].isdigit():
        return texto[:-2]
    return texto


def _parse_data(valor: Any) -> Optional[date]:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    if not texto:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(valor, dayfirst=True).date()
    except Exception:
        return None


def _parse_valor(valor: Any) -> Optional[float]:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if isinstance(valor, (int, float)) and not pd.isna(valor):
        return float(valor)
    texto = str(valor).strip()
    if not texto:
        return None
    texto = re.sub(r"[Rr]\$\s*", "", texto).replace(" ", "")
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _validar_extensao(nome_arquivo: str) -> None:
    ext = Path(nome_arquivo).suffix.lower()
    if ext not in EXTENSOES_VALIDAS:
        raise ValueError(f"Extensão inválida ({ext}). Use CSV, XLSX ou XLS.")


def _validar_arquivo(conteudo: bytes, nome_arquivo: str) -> None:
    if not conteudo:
        raise ValueError("Arquivo vazio.")
    if not nome_arquivo or not nome_arquivo.strip():
        raise ValueError("Nome do arquivo inválido.")
    _validar_extensao(nome_arquivo)


def _tratar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    base = _mapear_colunas(df)

    base["nf_nfd"] = base["nf_nfd"].apply(_sanitizar_nf)
    for col in ("cliente", "cidade", "bairro", "vendedor"):
        base[col] = base[col].apply(lambda v: _sanitizar_texto(v))
    base["cod_cliente"] = base["cod_cliente"].apply(lambda v: _sanitizar_texto(v, upper=True))
    base["data_emissao_nf"] = base["data_emissao_nf"].apply(_parse_data)
    base["valor_nf"] = base["valor_nf"].apply(_parse_valor)

    base = base[base["nf_nfd"].notna() & (base["nf_nfd"] != "")]
    if base.empty:
        raise ValueError("Nenhuma linha válida com NF encontrada na planilha.")

    if base["valor_nf"].isna().all():
        raise ValueError("Coluna ValorNF sem valores numéricos válidos.")

    for col in ("cod_cliente", "cliente", "cidade", "bairro", "vendedor"):
        base = base[base[col].notna() & (base[col] != "")]

    if base.empty:
        raise ValueError("Nenhuma linha completa após validação dos campos obrigatórios.")

    base = base.dropna(subset=["data_emissao_nf"], how="all")
    if base["data_emissao_nf"].isna().any():
        base = base[base["data_emissao_nf"].notna()]

    if base.empty:
        raise ValueError("Coluna DataNF sem datas válidas nas linhas importáveis.")

    base = base.drop_duplicates(subset=["nf_nfd"], keep="last")
    return base.reset_index(drop=True)


def _dataframe_para_registros(df: pd.DataFrame, nome_arquivo: str) -> list[dict[str, Any]]:
    agora = datetime.utcnow()
    registros: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        registros.append(
            {
                "nf_nfd": row["nf_nfd"],
                "data_emissao_nf": row["data_emissao_nf"],
                "cod_cliente": row["cod_cliente"],
                "cliente": row["cliente"],
                "cidade": row["cidade"],
                "bairro": row["bairro"],
                "vendedor": row["vendedor"],
                "valor_nf": row["valor_nf"],
                "arquivo_origem": nome_arquivo,
                "data_importacao": agora,
            }
        )
    return registros


def _backup_pasta_sap() -> Optional[Path]:
    UPLOADS_SAP_DIR.mkdir(parents=True, exist_ok=True)
    arquivos = [f for f in UPLOADS_SAP_DIR.iterdir() if f.is_file()]
    if not arquivos:
        return None

    backup_dir = UPLOADS_SAP_DIR / ".backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(parents=True)
    for arq in arquivos:
        shutil.copy2(arq, backup_dir / arq.name)
    return backup_dir


def _restaurar_pasta_sap(backup_dir: Optional[Path]) -> None:
    if backup_dir is None or not backup_dir.exists():
        return
    for arq in UPLOADS_SAP_DIR.iterdir():
        if arq.is_file():
            arq.unlink()
    for arq in backup_dir.iterdir():
        if arq.is_file():
            shutil.copy2(arq, UPLOADS_SAP_DIR / arq.name)
    shutil.rmtree(backup_dir, ignore_errors=True)


def _limpar_pasta_sap() -> None:
    UPLOADS_SAP_DIR.mkdir(parents=True, exist_ok=True)
    for arq in UPLOADS_SAP_DIR.iterdir():
        if arq.is_file():
            arq.unlink()
    backup = UPLOADS_SAP_DIR / ".backup"
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)


def salvar_arquivo_fisico(nome_arquivo: str, conteudo: bytes) -> Path:
    UPLOADS_SAP_DIR.mkdir(parents=True, exist_ok=True)
    destino = UPLOADS_SAP_DIR / Path(nome_arquivo).name
    destino.write_bytes(conteudo)
    return destino


def ler_arquivo_upload(conteudo: bytes, nome_arquivo: str) -> pd.DataFrame:
    nome = nome_arquivo.lower()
    buffer = io.BytesIO(conteudo)

    if nome.endswith(".csv"):
        ultimo_erro: Exception | None = None
        for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                buffer.seek(0)
                df = pd.read_csv(buffer, encoding=encoding)
                if not df.empty:
                    return df
            except Exception as exc:
                ultimo_erro = exc
        if ultimo_erro:
            raise ValueError(f"Não foi possível ler o CSV. Verifique o encoding. ({ultimo_erro})")
        raise ValueError("Planilha CSV vazia.")

    df = pd.read_excel(buffer, engine="openpyxl")
    if df.empty:
        raise ValueError("Planilha Excel vazia.")
    return df


def importar_planilha(
    conteudo: bytes,
    nome_arquivo: str,
    usuario: str = "sistema",
) -> tuple[bool, str, int, Optional[pd.DataFrame]]:
    """
    Substitui integralmente a base SAP (arquivo + banco).
    Retorna: sucesso, mensagem, quantidade, dataframe para preview.
    """
    backup_db: list[dict[str, Any]] = []
    backup_dir: Optional[Path] = None

    try:
        _validar_arquivo(conteudo, nome_arquivo)
        df_raw = ler_arquivo_upload(conteudo, nome_arquivo)
        df_tratado = _tratar_dataframe(df_raw)
        registros = _dataframe_para_registros(df_tratado, Path(nome_arquivo).name)

        backup_db = sap_repository.listar_todos_como_dicts()
        backup_dir = _backup_pasta_sap()

        qtd = sap_repository.substituir_base_completa(registros)

        _limpar_pasta_sap()
        salvar_arquivo_fisico(nome_arquivo, conteudo)

        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)

        log_import_sap(usuario, nome_arquivo, qtd, True, detalhe="substituicao_total")
        limpar_cache_leitura()
        return True, MSG_SUCESSO, qtd, df_tratado

    except Exception as exc:
        try:
            if backup_db:
                sap_repository.substituir_base_completa(backup_db)
            _restaurar_pasta_sap(backup_dir)
        except Exception as restore_exc:
            log_import_sap(
                usuario,
                nome_arquivo,
                0,
                False,
                detalhe=f"falha_restauracao={restore_exc}",
                erro=restore_exc,
            )

        log_import_sap(usuario, nome_arquivo, 0, False, detalhe=str(exc), erro=exc)
        return False, f"{MSG_ERRO} {exc}", 0, None


def _obter_por_nf_db(nf_nfd: str) -> tuple[bool, str, Optional[dict[str, Any]]]:
    chave = _sanitizar_nf(nf_nfd)
    if not chave:
        return False, "Informe o número NF/NFD.", None

    dados = sap_repository.buscar_por_nf(chave)
    if dados is None:
        return False, "Número NF não localizado na base SAP.", None

    if dados.get("data_emissao_nf") and isinstance(dados["data_emissao_nf"], str):
        from core.orm_serialize import parse_iso_date

        dados = {**dados, "data_emissao_nf": parse_iso_date(dados["data_emissao_nf"])}

    if not dados.get("nf_nfd"):
        return False, "Dados SAP inválidos para esta NF/NFD.", None

    return True, "Dados SAP localizados.", dados


@st.cache_data(ttl=TTL_SAP, show_spinner=False)
def buscar_nf_cache(nf_nfd: str) -> tuple[bool, str, Optional[dict[str, Any]]]:
    return _obter_por_nf_db(nf_nfd)


def obter_por_nf(nf_nfd: str) -> tuple[bool, str, Optional[dict[str, Any]]]:
    return buscar_nf_cache(_sanitizar_nf(nf_nfd) or str(nf_nfd or "").strip())


@st.cache_data(ttl=TTL_SAP, show_spinner=False)
def contar_base_cache() -> int:
    return sap_repository.contar_registros()


def contar_base() -> int:
    return contar_base_cache()


@st.cache_data(ttl=TTL_SAP, show_spinner=False)
def obter_arquivo_ativo_cache() -> Optional[str]:
    UPLOADS_SAP_DIR.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(
        (f for f in UPLOADS_SAP_DIR.iterdir() if f.is_file() and not f.name.startswith(".")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return arquivos[0].name if arquivos else None


def obter_arquivo_ativo() -> Optional[str]:
    return obter_arquivo_ativo_cache()
