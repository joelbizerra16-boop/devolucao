"""Ambiente de execução do DEVOLUÇÃO.

Fonte única para development, production e test.
Não abre conexão e não registra segredos.
"""

from __future__ import annotations

import os

ENV_VAR = "DEVOLUCAO_ENV"
ENV_DEVELOPMENT = "development"
ENV_PRODUCTION = "production"
ENV_TEST = "test"
VALID_ENVS = frozenset({ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_TEST})

AUTH_SECRET_VAR = "DEVOLUCAO_AUTH_SECRET"
DEV_AUTH_SECRET = "devolucao-wms-local-secret-altere-em-producao"

DATABASE_URL_VAR = "DATABASE_URL"

SSLMODE_VAR = "DB_SSLMODE"
DEFAULT_SSLMODE = "require"
VALID_SSLMODES = frozenset(
    {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
)


class ProductionConfigError(RuntimeError):
    """Configuração inválida. A mensagem não contém senha, URL nem segredo."""


def current_env() -> str:
    raw = (os.getenv(ENV_VAR) or ENV_DEVELOPMENT).strip().lower()
    if raw not in VALID_ENVS:
        raise ProductionConfigError(
            f"{ENV_VAR} inválido ({raw!r}). Use development, production ou test."
        )
    return raw


def is_production() -> bool:
    return current_env() == ENV_PRODUCTION


def is_development() -> bool:
    return current_env() == ENV_DEVELOPMENT


def is_test() -> bool:
    return current_env() == ENV_TEST


def expose_technical_errors() -> bool:
    """Traceback na interface somente fora de production."""
    try:
        return not is_production()
    except ProductionConfigError:
        return False


def database_url_raw() -> str:
    return (os.getenv(DATABASE_URL_VAR) or "").strip()


def require_production_database_url() -> None:
    if not is_production():
        return
    url = database_url_raw()
    if not url:
        raise ProductionConfigError(
            "DATABASE_URL é obrigatória quando DEVOLUCAO_ENV=production "
            "e está ausente ou vazia. A aplicação não inicia e não utiliza SQLite em produção."
        )
    normalized = url
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized[len("postgres://") :]
    if not normalized.startswith("postgresql://"):
        raise ProductionConfigError(
            "DATABASE_URL em production deve ser PostgreSQL (postgresql://). "
            "SQLite é proibido em produção."
        )


def resolve_auth_secret() -> str:
    raw = (os.getenv(AUTH_SECRET_VAR) or "").strip()
    if is_production():
        if not raw:
            raise ProductionConfigError(
                "DEVOLUCAO_AUTH_SECRET é obrigatória quando DEVOLUCAO_ENV=production "
                "e está ausente ou vazia."
            )
        if raw == DEV_AUTH_SECRET:
            raise ProductionConfigError(
                "DEVOLUCAO_AUTH_SECRET não pode usar o valor padrão de desenvolvimento em production."
            )
        return raw
    return raw or DEV_AUTH_SECRET


def resolve_sslmode() -> str:
    raw = (os.getenv(SSLMODE_VAR) or "").strip().lower()
    if not raw:
        return DEFAULT_SSLMODE
    if raw not in VALID_SSLMODES:
        raise ProductionConfigError(
            f"{SSLMODE_VAR} inválido ({raw!r}). "
            "Use disable, allow, prefer, require, verify-ca ou verify-full."
        )
    return raw


def startup_error() -> str | None:
    """Mensagem segura de configuração, ou None quando o processo pode continuar."""
    try:
        current_env()
        require_production_database_url()
        if is_production():
            resolve_auth_secret()
    except ProductionConfigError as exc:
        return str(exc)
    return None
