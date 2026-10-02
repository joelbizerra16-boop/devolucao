"""Regras de produção: banco, SSL, segredo, admin padrão, logs e diretórios."""

from __future__ import annotations

import os
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.environment import (
    DEV_AUTH_SECRET,
    ProductionConfigError,
    resolve_auth_secret,
    resolve_sslmode,
    startup_error,
)
from core.paths import DATA_DIR, LOGS_DIR, UPLOADS_DIR, UPLOADS_SAP_DIR, ensure_runtime_dirs
from core.redaction import redact_secrets
from database.connection import (
    _pool_kwargs,
    _resolve_database_url,
    postgres_connect_args,
    sqlalchemy_url,
)
from database.models import Base, Usuario
from scripts.validate_database import configuration_error


class DatabaseUrlRulesTests(unittest.TestCase):
    def test_production_sem_database_url_falha(self) -> None:
        with patch.dict(os.environ, {"DEVOLUCAO_ENV": "production", "DATABASE_URL": ""}, clear=False):
            with self.assertRaises(ProductionConfigError) as ctx:
                _resolve_database_url()
        message = str(ctx.exception)
        self.assertIn("DATABASE_URL", message)
        self.assertNotIn("postgresql://", message)
        self.assertNotIn("admin123", message)

    def test_development_sem_database_url_usa_sqlite(self) -> None:
        with patch.dict(os.environ, {"DEVOLUCAO_ENV": "development"}, clear=False):
            os.environ.pop("DATABASE_URL", None)
            url = _resolve_database_url()
        self.assertTrue(url.startswith("sqlite:///"))
        self.assertIn("devolucao.db", url)

    def test_production_rejeita_sqlite(self) -> None:
        with patch.dict(
            os.environ,
            {"DEVOLUCAO_ENV": "production", "DATABASE_URL": "sqlite:///tmp/devolucao.db"},
            clear=False,
        ):
            with self.assertRaises(ProductionConfigError):
                _resolve_database_url()

    def test_production_aceita_postgresql_sem_criar_sqlite(self) -> None:
        url_in = "postgresql://devolucao_user:x@devolucao-postgres:5432/devolucao"
        with patch.dict(
            os.environ,
            {"DEVOLUCAO_ENV": "production", "DATABASE_URL": url_in},
            clear=False,
        ):
            url = _resolve_database_url()
        parsed = urlparse(url)
        self.assertEqual(parsed.scheme, "postgresql")
        self.assertEqual(parsed.hostname, "devolucao-postgres")
        self.assertNotIn("sqlite", url)

    def test_sslmode_configurado_e_respeitado(self) -> None:
        with patch.dict(os.environ, {"DB_SSLMODE": "disable", "DB_CONNECT_TIMEOUT": "7"}, clear=False):
            self.assertEqual(resolve_sslmode(), "disable")
            args = postgres_connect_args()
        self.assertEqual(args["sslmode"], "disable")
        self.assertEqual(args["connect_timeout"], 7)

        with patch.dict(os.environ, {"DB_SSLMODE": "require"}, clear=False):
            self.assertEqual(resolve_sslmode(), "require")
            self.assertEqual(postgres_connect_args()["sslmode"], "require")

    def test_sslmode_padrao_permanece_require(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DB_SSLMODE", None)
            self.assertEqual(resolve_sslmode(), "require")

    def test_url_interna_usa_psycopg2_sem_alterar_host(self) -> None:
        url = sqlalchemy_url("postgresql://devolucao_user:x@devolucao-postgres:5432/devolucao")
        parsed = urlparse(url)
        self.assertTrue(url.startswith("postgresql+psycopg2://"))
        self.assertEqual(parsed.hostname, "devolucao-postgres")
        self.assertEqual(parsed.path, "/devolucao")

    def test_pool_permanece_configuravel(self) -> None:
        with patch.dict(
            os.environ,
            {"DB_POOL_SIZE": "3", "DB_POOL_MAX_OVERFLOW": "4", "DB_POOL_RECYCLE": "120"},
            clear=False,
        ):
            pool = _pool_kwargs()
        self.assertEqual(pool["pool_size"], 3)
        self.assertEqual(pool["max_overflow"], 4)
        self.assertEqual(pool["pool_recycle"], 120)


class AuthSecretRulesTests(unittest.TestCase):
    def test_production_sem_segredo_falha(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DEVOLUCAO_ENV": "production",
                "DATABASE_URL": "postgresql://devolucao_user:x@devolucao-postgres:5432/devolucao",
                "DEVOLUCAO_AUTH_SECRET": "",
            },
            clear=False,
        ):
            with self.assertRaises(ProductionConfigError) as ctx:
                resolve_auth_secret()
            message = startup_error()
        self.assertIn("DEVOLUCAO_AUTH_SECRET", str(ctx.exception))
        self.assertIn("DEVOLUCAO_AUTH_SECRET", message or "")
        self.assertNotIn(DEV_AUTH_SECRET, message or "")

    def test_production_rejeita_segredo_padrao(self) -> None:
        with patch.dict(
            os.environ,
            {"DEVOLUCAO_ENV": "production", "DEVOLUCAO_AUTH_SECRET": DEV_AUTH_SECRET},
            clear=False,
        ):
            with self.assertRaises(ProductionConfigError) as ctx:
                resolve_auth_secret()
        self.assertNotIn(DEV_AUTH_SECRET, str(ctx.exception))

    def test_development_aceita_segredo_padrao(self) -> None:
        with patch.dict(os.environ, {"DEVOLUCAO_ENV": "development"}, clear=False):
            os.environ.pop("DEVOLUCAO_AUTH_SECRET", None)
            secret = resolve_auth_secret()
        self.assertEqual(secret, DEV_AUTH_SECRET)


class AdminSeedRulesTests(unittest.TestCase):
    def test_production_nao_cria_admin_padrao(self) -> None:
        from database.migrations import seed_usuario_admin
        from services.usuario_service import seed_default_users

        with patch.dict(os.environ, {"DEVOLUCAO_ENV": "production"}, clear=False):
            with patch("database.migrations.get_write_session") as session_scope:
                seed_usuario_admin()
            session_scope.assert_not_called()
            with patch("services.usuario_service.usuario_repository.buscar_por_username") as buscar:
                with patch("services.usuario_service.usuario_repository.inserir") as inserir:
                    seed_default_users()
            buscar.assert_not_called()
            inserir.assert_not_called()

    def test_development_mantem_seed_admin(self) -> None:
        from database.migrations import seed_usuario_admin
        from services.usuario_service import seed_default_users

        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine, expire_on_commit=False)

        @contextmanager
        def scope():
            session = factory()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

        with patch.dict(os.environ, {"DEVOLUCAO_ENV": "development"}, clear=False):
            with patch("database.migrations.get_write_session", scope):
                seed_usuario_admin()
            with patch("services.usuario_service.usuario_repository.buscar_por_username", return_value=None):
                with patch("services.usuario_service.usuario_repository.inserir") as inserir:
                    seed_default_users()
            self.assertTrue(inserir.called)
            senha_hash = inserir.call_args.kwargs["senha_hash"]

        with scope() as session:
            user = session.query(Usuario).filter(Usuario.username == "admin").one()
        self.assertEqual(user.username, "admin")
        self.assertNotEqual(user.senha_hash, "admin123")
        self.assertTrue(bcrypt.checkpw(b"admin123", user.senha_hash.encode("utf-8")))
        self.assertNotEqual(senha_hash, "admin123")
        self.assertTrue(bcrypt.checkpw(b"admin123", senha_hash.encode("utf-8")))
        engine.dispose()


class RuntimeAndLogTests(unittest.TestCase):
    def test_diretorios_runtime_sao_criados(self) -> None:
        ensure_runtime_dirs()
        for path in (DATA_DIR, UPLOADS_DIR, UPLOADS_SAP_DIR, LOGS_DIR):
            self.assertTrue(path.is_dir(), str(path))

    def test_logs_nao_exibem_segredo_nem_senha_da_url(self) -> None:
        import core.system_log as slog

        secret = "segredo-de-teste-123456"
        url = f"postgresql://devolucao_user:{secret}@devolucao-postgres:5432/devolucao"
        message = f"{url} auth=token-de-teste cookie devolucao_auth=cookie-de-teste"
        with patch.dict(
            os.environ,
            {"DEVOLUCAO_ENV": "development", "DEVOLUCAO_AUTH_SECRET": secret},
            clear=False,
        ):
            redacted = redact_secrets(message)
            log_dir = ROOT / "logs"
            log_file = log_dir / "guardrail-test.log"
            with patch.object(slog, "LOG_DIR", log_dir), patch.object(slog, "LOG_FILE", log_file):
                slog.log_event("db", message)
        self.assertNotIn(secret, redacted)
        self.assertNotIn("token-de-teste", redacted)
        self.assertNotIn("cookie-de-teste", redacted)
        stored = log_file.read_text(encoding="utf-8")
        self.assertNotIn(secret, stored)
        self.assertNotIn("token-de-teste", stored)
        self.assertIn("***", stored)
        log_file.unlink(missing_ok=True)

    def test_validador_nao_le_sem_database_url(self) -> None:
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            error = configuration_error()
        self.assertIsNotNone(error)
        self.assertIn("DATABASE_URL", error or "")


if __name__ == "__main__":
    unittest.main()
