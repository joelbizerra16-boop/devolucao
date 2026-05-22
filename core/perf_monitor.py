"""
Monitoramento interno de performance — logs discretos (sem UI).

Ativar: PERF_MONITOR=1 (padrão). Limiar: PERF_SLOW_MS (padrão 400ms).
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Generator

from core.system_log import log_event

_PERF_ENABLED = os.getenv("PERF_MONITOR", "1").strip().lower() not in (
    "0",
    "false",
    "no",
    "off",
)
_SLOW_MS = float(os.getenv("PERF_SLOW_MS", "400"))


@contextmanager
def track(scope: str, label: str) -> Generator[None, None, None]:
    """Registra operações lentas em logs/system.log."""
    if not _PERF_ENABLED:
        yield
        return
    t0 = time.perf_counter()
    try:
        yield
    finally:
        ms = (time.perf_counter() - t0) * 1000.0
        if ms >= _SLOW_MS:
            log_event("perf", f"{scope}:{label} {ms:.0f}ms")


def track_page(page: str) -> contextmanager:
    return track("page", page)


def track_query(name: str) -> contextmanager:
    return track("query", name)
