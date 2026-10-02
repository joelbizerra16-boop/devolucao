"""Caminhos centralizados de dados e uploads."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_SAP_DIR = UPLOADS_DIR / "sap"

LOGS_DIR = BASE_DIR / "logs"

DEVOLUCOES_CSV = DATA_DIR / "devolucoes.csv"
MOTIVOS_CSV = DATA_DIR / "motivos.csv"


def ensure_runtime_dirs() -> None:
    """Cria diretórios de runtime sem apagar conteúdo existente."""
    for path in (DATA_DIR, UPLOADS_DIR, UPLOADS_SAP_DIR, LOGS_DIR):
        path.mkdir(parents=True, exist_ok=True)

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
