"""Log temporário de erros do sistema — logs/system.log"""

from __future__ import annotations

import traceback
from datetime import datetime
from pathlib import Path

from core.redaction import redact_secrets

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "system.log"


def log_event(categoria: str, mensagem: str, exc: Exception | None = None) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        linha = f"[{datetime.now().isoformat(timespec='seconds')}] [{categoria}] {mensagem}"
        if exc is not None:
            linha += f"\n{traceback.format_exc()}"
        linha = redact_secrets(linha)
        with LOG_FILE.open("a", encoding="utf-8") as arquivo:
            arquivo.write(linha + "\n")
    except Exception:
        pass
