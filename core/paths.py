"""Caminhos centralizados de dados e uploads."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_SAP_DIR = UPLOADS_DIR / "sap"

DEVOLUCOES_CSV = DATA_DIR / "devolucoes.csv"
MOTIVOS_CSV = DATA_DIR / "motivos.csv"

DEVOLUCOES_COLUNAS = [
    "d_devolucao",
    "nf",
    "motivo",
    "observacao",
    "responsavel",
    "data_registro",
]

MOTIVOS_COLUNAS = ["id", "descricao"]

MOTIVOS_PADRAO = [
    "Avaria no transporte",
    "Produto divergente",
    "Pedido cancelado",
    "Validade próxima",
    "Embalagem danificada",
]
