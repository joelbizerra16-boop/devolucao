"""Mascaramento de segredos antes de log ou mensagem técnica."""

from __future__ import annotations

import os
import re

from core.environment import AUTH_SECRET_VAR, DEV_AUTH_SECRET

_POSTGRES_URL_RE = re.compile(
    r"(postgres(?:ql)?://)([^:\s/@]+):([^@\s/]+)@",
    re.IGNORECASE,
)
_AUTH_QUERY_RE = re.compile(r"([?&\s]auth=)[^&\s]+", re.IGNORECASE)
_COOKIE_RE = re.compile(r"(devolucao_auth=)[^;\s]+", re.IGNORECASE)
_BCRYPT_RE = re.compile(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}")


def _replace_known_secret(text: str, secret: str) -> str:
    cleaned = secret.strip()
    if len(cleaned) < 8 or cleaned not in text:
        return text
    return text.replace(cleaned, "***")


def redact_secrets(text: str) -> str:
    if not text:
        return text
    redacted = _POSTGRES_URL_RE.sub(r"\1\2:***@", text)
    redacted = _AUTH_QUERY_RE.sub(r"\1***", redacted)
    redacted = _COOKIE_RE.sub(r"\1***", redacted)
    redacted = _BCRYPT_RE.sub("***", redacted)
    redacted = _replace_known_secret(redacted, os.getenv(AUTH_SECRET_VAR, ""))
    redacted = _replace_known_secret(redacted, os.getenv("POSTGRES_PASSWORD", ""))
    redacted = _replace_known_secret(redacted, DEV_AUTH_SECRET)
    return redacted
