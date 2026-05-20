"""Log de importações SAP — logs/import_sap.log"""

from __future__ import annotations

import traceback
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "import_sap.log"


def log_import_sap(
    usuario: str,
    arquivo: str,
    registros: int,
    sucesso: bool,
    detalhe: str = "",
    erro: Exception | None = None,
) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        status = "SUCESSO" if sucesso else "ERRO"
        linha = (
            f"[{datetime.now().isoformat(timespec='seconds')}] "
            f"[{status}] usuario={usuario} arquivo={arquivo} registros={registros} {detalhe}"
        )
        if erro is not None:
            linha += f"\n{traceback.format_exc()}"
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass
