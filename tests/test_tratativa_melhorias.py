"""Testes das melhorias de tratativa — filtro, indicadores e rastreabilidade."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.auth import UserSession
from core.constants import (
    PERFIL_ADMIN_DB,
    PERFIL_VISITANTE_DB,
    TRATATIVA_FILTRO_TODOS,
)
from core.tratativa_utils import (
    calcular_indicadores_tratativa,
    classificar_tratativa,
    filtrar_linhas_por_tratativa,
    tratativa_corresponde_filtro,
)
from database.models import Base, Devolucao
from database.migrations import seed_motivos_padrao, seed_usuario_admin
from repositories import devolucao_repository
from services.dashboard_service import (
    listar_devolucoes_periodo_dashboard,
    obter_indicadores_tratativa_dashboard,
)
from services.devolucao_service import atualizar_tratativa

_TEST_ENGINE = None
_TEST_SESSION_FACTORY = None
_TEST_DB_PATH: str | None = None
_DB_READY = False

_VISITANTE = UserSession(
    id=2,
    username="visit",
    nome="Maria Visitante",
    perfil=PERFIL_VISITANTE_DB,
)


@contextmanager
def _test_session_scope(*, read_only: bool = False):
    session = _TEST_SESSION_FACTORY()
    try:
        yield session
        if read_only:
            if session.new or session.dirty or session.deleted:
                session.rollback()
        else:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _setup_test_db() -> None:
    global _TEST_ENGINE, _TEST_SESSION_FACTORY, _TEST_DB_PATH, _DB_READY
    if _DB_READY:
        return
    fd, _TEST_DB_PATH = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{_TEST_DB_PATH}"
    _TEST_ENGINE = create_engine(url, connect_args={"check_same_thread": False})
    _TEST_SESSION_FACTORY = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_TEST_ENGINE,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=_TEST_ENGINE)
    _DB_READY = True


def _dispose_test_db() -> None:
    global _TEST_ENGINE, _TEST_DB_PATH, _DB_READY
    if _TEST_ENGINE is not None:
        _TEST_ENGINE.dispose()
        _TEST_ENGINE = None
    if _TEST_DB_PATH and os.path.exists(_TEST_DB_PATH):
        try:
            os.unlink(_TEST_DB_PATH)
        except OSError:
            pass
    _TEST_DB_PATH = None
    _DB_READY = False


def _seed_test_db() -> None:
    seed_motivos_padrao()
    seed_usuario_admin()


def _inserir(**kwargs) -> int:
    dados = {
        "data_devolucao": date(2026, 6, 17),
        "usuario": "Juliana",
        "motivo_devolucao": "Cliente não fez pedido",
        "nf_nfd": "1423300",
        "observacao": None,
    }
    dados.update(kwargs)
    return devolucao_repository.inserir(**dados)


class TratativaMelhoriasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _setup_test_db()
        cls._patches = [
            patch("core.db.get_engine", return_value=_TEST_ENGINE),
            patch("core.db.get_session", side_effect=lambda **kw: _test_session_scope(read_only=True)),
            patch("core.db.get_write_session", side_effect=lambda: _test_session_scope(read_only=False)),
            patch(
                "repositories.devolucao_repository.get_session",
                side_effect=lambda **kw: _test_session_scope(read_only=True),
            ),
            patch(
                "repositories.devolucao_repository.get_write_session",
                side_effect=lambda: _test_session_scope(read_only=False),
            ),
            patch("database.migrations.get_engine", return_value=_TEST_ENGINE),
            patch(
                "database.migrations.get_write_session",
                side_effect=lambda: _test_session_scope(read_only=False),
            ),
            patch(
                "services.dashboard_service.listar_devolucoes_periodo_cache",
                side_effect=cls._listar_cache_local,
            ),
        ]
        for p in cls._patches:
            p.start()
        _seed_test_db()
        cls._rows_fixture: list[dict] = []

    @classmethod
    def _listar_cache_local(cls, mes: int, ano: int, busca: str = "") -> tuple[dict, ...]:
        return tuple(cls._rows_fixture)

    @classmethod
    def tearDownClass(cls) -> None:
        for p in cls._patches:
            p.stop()
        _dispose_test_db()

    def setUp(self) -> None:
        TratativaMelhoriasTests._rows_fixture = [
            {"id": 1, "data_devolucao": "2026-06-17", "tratativa": "Aguardando", "motivo_devolucao": "A"},
            {"id": 2, "data_devolucao": "2026-06-17", "tratativa": "Em análise", "motivo_devolucao": "B"},
            {"id": 3, "data_devolucao": "2026-06-17", "tratativa": "Concluído", "motivo_devolucao": "C"},
            {"id": 4, "data_devolucao": "2026-06-17", "tratativa": "Recusado pelo cliente", "motivo_devolucao": "D"},
        ]
        with _test_session_scope(read_only=False) as session:
            session.query(Devolucao).delete()

    def test_01_filtro_por_tratativa(self) -> None:
        self.assertTrue(tratativa_corresponde_filtro("Aguardando", "Aguardando"))
        self.assertFalse(tratativa_corresponde_filtro("Concluído", "Aguardando"))

        filtradas = filtrar_linhas_por_tratativa(self._rows_fixture, "Em Análise")
        self.assertEqual(len(filtradas), 1)
        self.assertEqual(filtradas[0]["id"], 2)

        lista = listar_devolucoes_periodo_dashboard(6, 2026, tratativa_filtro="Concluído")
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0].tratativa, "Concluído")

        todas = listar_devolucoes_periodo_dashboard(6, 2026, tratativa_filtro=TRATATIVA_FILTRO_TODOS)
        self.assertEqual(len(todas), 4)

    def test_02_cards_exibem_valores_corretos(self) -> None:
        indicadores = obter_indicadores_tratativa_dashboard(6, 2026)
        self.assertEqual(indicadores["total_devolucoes"], "4")
        self.assertEqual(indicadores["total_aguardando"], "1")
        self.assertEqual(indicadores["total_em_analise"], "1")
        self.assertEqual(indicadores["total_concluido"], "1")
        self.assertEqual(indicadores["total_recusado"], "1")

        filtrado = obter_indicadores_tratativa_dashboard(6, 2026, tratativa_filtro="Aguardando")
        self.assertEqual(filtrado["total_devolucoes"], "1")
        self.assertEqual(filtrado["total_aguardando"], "1")
        self.assertEqual(filtrado["total_em_analise"], "0")

    @patch("services.devolucao_service.get_current_user", return_value=_VISITANTE)
    @patch("services.devolucao_service.pode_editar_tratativa", return_value=True)
    def test_03_atualizacao_grava_usuario(self, _perm, _user) -> None:
        dev_id = _inserir(nf_nfd="9001")
        ok, _ = atualizar_tratativa(dev_id, "Em análise")
        self.assertTrue(ok)
        dev = devolucao_repository.obter_por_id(dev_id)
        self.assertEqual(getattr(dev, "tratativa_atualizada_por", None), "Maria Visitante")

    @patch("services.devolucao_service.get_current_user", return_value=_VISITANTE)
    @patch("services.devolucao_service.pode_editar_tratativa", return_value=True)
    def test_04_atualizacao_grava_data_hora(self, _perm, _user) -> None:
        antes = datetime.utcnow()
        dev_id = _inserir(nf_nfd="9002")
        ok, _ = atualizar_tratativa(dev_id, "Concluído")
        self.assertTrue(ok)
        dev = devolucao_repository.obter_por_id(dev_id)
        gravado = getattr(dev, "tratativa_atualizada_em", None)
        self.assertIsNotNone(gravado)
        self.assertGreaterEqual(gravado, antes)

    def test_05_registros_antigos_permanecem_compativeis(self) -> None:
        dev_id = _inserir(nf_nfd="9003")
        dev = devolucao_repository.obter_por_id(dev_id)
        self.assertIsNone(getattr(dev, "tratativa_atualizada_em", None))
        self.assertIsNone(getattr(dev, "tratativa_atualizada_por", None))
        self.assertEqual(getattr(dev, "tratativa", None), "Aguardando")

    @patch("services.devolucao_service.pode_editar_tratativa", return_value=False)
    def test_06_permissoes_continuam_funcionando(self, _perm) -> None:
        dev_id = _inserir(nf_nfd="9004")
        ok, msg = atualizar_tratativa(dev_id, "Recusado")
        self.assertFalse(ok)
        self.assertIn("Permissão negada", msg)

    @patch("core.permissions.get_current_user")
    def test_06b_admin_nao_edita_tratativa(self, mock_user) -> None:
        mock_user.return_value = UserSession(
            id=1, username="admin", nome="Admin", perfil=PERFIL_ADMIN_DB
        )
        from core.permissions import pode_editar_tratativa

        self.assertFalse(pode_editar_tratativa())

    def test_07_dashboard_mantem_performance_sem_consulta_extra(self) -> None:
        """Indicadores calculados em memória a partir do cache da listagem."""
        calls = {"cache": 0}
        original = TratativaMelhoriasTests._listar_cache_local

        def contador(mes, ano, busca=""):
            calls["cache"] += 1
            return original(mes, ano, busca)

        with patch(
            "services.dashboard_service.listar_devolucoes_periodo_cache",
            side_effect=contador,
        ):
            listar_devolucoes_periodo_dashboard(6, 2026, tratativa_filtro="Todos")
            obter_indicadores_tratativa_dashboard(6, 2026, tratativa_filtro="Todos")

        self.assertEqual(calls["cache"], 2)
        raw = calcular_indicadores_tratativa(self._rows_fixture)
        self.assertEqual(classificar_tratativa("Resolvido"), "Concluído")


if __name__ == "__main__":
    unittest.main()
