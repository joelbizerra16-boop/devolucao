"""Testes da funcionalidade de tratativa em devoluções."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.constants import PERFIL_ADMIN_DB, PERFIL_VISITANTE_DB, TRATATIVA_PADRAO
from core.auth import UserSession
from components.listagem_dashboard import COLUNAS_LISTVIEW_OPERACIONAL, _linha_para_exibicao
from database.models import Base, Devolucao
from database.migrations import _migrar_coluna_tratativa, seed_motivos_padrao, seed_usuario_admin
from repositories import devolucao_repository
from services.devolucao_service import atualizar_tratativa

_TEST_ENGINE = None
_TEST_SESSION_FACTORY = None
_TEST_DB_PATH: str | None = None
_DB_READY = False


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


def _inserir_devolucao_fixture(**kwargs) -> int:
    dados = {
        "data_devolucao": date(2026, 6, 17),
        "usuario": "Juliana",
        "motivo_devolucao": "Cliente não fez pedido",
        "nf_nfd": "1423300",
        "observacao": None,
        "cod_cliente": "C027189",
        "vendedor": "Daiane Carrasco De Pinho",
        "valor_nf": 216.36,
    }
    dados.update(kwargs)
    return devolucao_repository.inserir(**dados)


def _snapshot_devolucao(devolucao_id: int) -> dict:
    dev = devolucao_repository.obter_por_id(devolucao_id)
    assert dev is not None
    return {
        "data_devolucao": dev.data_devolucao,
        "usuario": dev.usuario,
        "usuario_ultima_edicao": dev.usuario_ultima_edicao,
        "motivo_devolucao": dev.motivo_devolucao,
        "nf_nfd": dev.nf_nfd,
        "valor_nf": dev.valor_nf,
        "cod_cliente": dev.cod_cliente,
        "vendedor": dev.vendedor,
        "observacao": dev.observacao,
        "tratativa": getattr(dev, "tratativa", None),
        "tratativa_atualizada_em": getattr(dev, "tratativa_atualizada_em", None),
        "tratativa_atualizada_por": getattr(dev, "tratativa_atualizada_por", None),
    }


class TratativaTests(unittest.TestCase):
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
        ]
        for p in cls._patches:
            p.start()
        _seed_test_db()

    @classmethod
    def tearDownClass(cls) -> None:
        for p in cls._patches:
            p.stop()
        _dispose_test_db()

    def setUp(self) -> None:
        with _test_session_scope(read_only=False) as session:
            session.query(Devolucao).delete()

    def test_01_registro_novo_recebe_aguardando(self) -> None:
        dev_id = _inserir_devolucao_fixture()
        dev = devolucao_repository.obter_por_id(dev_id)
        self.assertIsNotNone(dev)
        self.assertEqual(getattr(dev, "tratativa", None), TRATATIVA_PADRAO)

    def test_02_registros_antigos_recebem_aguardando_apos_migration(self) -> None:
        with _test_session_scope(read_only=False) as session:
            dev = Devolucao(
                data_lancamento=date(2025, 1, 1),
                data_devolucao=date(2025, 1, 1),
                usuario="Legado",
                motivo_devolucao="Motivo legado",
                nf_nfd="999",
            )
            session.add(dev)
            session.flush()
            dev_id = int(dev.id)

        from sqlalchemy import text

        with _TEST_ENGINE.connect() as conn:
            conn.execute(text("UPDATE devolucoes SET tratativa = '' WHERE id = :id"), {"id": dev_id})
            conn.commit()

        with patch("core.db.get_engine", return_value=_TEST_ENGINE):
            with patch("database.migrations.get_engine", return_value=_TEST_ENGINE):
                _migrar_coluna_tratativa()

        dev = devolucao_repository.obter_por_id(dev_id)
        self.assertEqual(getattr(dev, "tratativa", None), TRATATIVA_PADRAO)

    def test_03_coluna_tratativa_aparece_na_listview(self) -> None:
        self.assertIn("Tratativa", COLUNAS_LISTVIEW_OPERACIONAL)
        idx_motivo = COLUNAS_LISTVIEW_OPERACIONAL.index("Motivo")
        idx_tratativa = COLUNAS_LISTVIEW_OPERACIONAL.index("Tratativa")
        idx_nf = COLUNAS_LISTVIEW_OPERACIONAL.index("NF")
        self.assertEqual(idx_tratativa, idx_motivo + 1)
        self.assertEqual(idx_nf, idx_tratativa + 1)

        row = SimpleNamespace(
            id=1,
            data_devolucao=date(2026, 6, 17),
            usuario="Juliana",
            usuario_ultima_edicao=None,
            motivo_devolucao="Cliente não fez pedido",
            tratativa="Em análise",
            nf_nfd="1423300",
            valor_nf=216.36,
            cod_cliente="C027189",
            vendedor="Vendedor",
        )
        dados = _linha_para_exibicao(row)
        self.assertEqual(dados["tratativa"], "Em análise")

    @patch("services.devolucao_service.pode_editar_tratativa", return_value=True)
    def test_04_visitante_consegue_abrir_fluxo_tratativa(self, _mock_perm) -> None:
        dev_id = _inserir_devolucao_fixture()
        dev = devolucao_repository.obter_por_id(dev_id)
        self.assertIsNotNone(dev)
        self.assertEqual(dev.motivo_devolucao, "Cliente não fez pedido")
        self.assertEqual(dev.nf_nfd, "1423300")

    @patch("services.devolucao_service.get_current_user", return_value=UserSession(
        id=2, username="visit", nome="Visitante Teste", perfil=PERFIL_VISITANTE_DB,
    ))
    @patch("services.devolucao_service.pode_editar_tratativa", return_value=True)
    def test_05_visitante_consegue_salvar(self, _mock_perm, _mock_user) -> None:
        dev_id = _inserir_devolucao_fixture()
        ok, msg = atualizar_tratativa(dev_id, "Em análise")
        self.assertTrue(ok, msg)
        dev = devolucao_repository.obter_por_id(dev_id)
        self.assertEqual(getattr(dev, "tratativa", None), "Em análise")

    @patch("services.devolucao_service.pode_editar_tratativa", return_value=False)
    def test_06_nao_visitante_recebe_acesso_negado(self, _mock_perm) -> None:
        dev_id = _inserir_devolucao_fixture()
        ok, msg = atualizar_tratativa(dev_id, "Resolvido")
        self.assertFalse(ok)
        self.assertIn("Permissão negada", msg)
        dev = devolucao_repository.obter_por_id(dev_id)
        self.assertEqual(getattr(dev, "tratativa", None), TRATATIVA_PADRAO)

    @patch("services.devolucao_service.get_current_user", return_value=UserSession(
        id=2, username="visit", nome="Visitante Teste", perfil=PERFIL_VISITANTE_DB,
    ))
    @patch("services.devolucao_service.pode_editar_tratativa", return_value=True)
    def test_07_somente_campo_tratativa_e_alterado(self, _mock_perm, _mock_user) -> None:
        dev_id = _inserir_devolucao_fixture()
        antes = _snapshot_devolucao(dev_id)
        ok, _ = atualizar_tratativa(dev_id, "Concluído")
        self.assertTrue(ok)
        depois = _snapshot_devolucao(dev_id)
        self.assertEqual(depois["tratativa"], "Concluído")
        for campo in (
            "data_devolucao",
            "usuario",
            "usuario_ultima_edicao",
            "motivo_devolucao",
            "nf_nfd",
            "valor_nf",
            "cod_cliente",
            "vendedor",
            "observacao",
        ):
            self.assertEqual(depois[campo], antes[campo], campo)

    @patch("services.devolucao_service.get_current_user", return_value=UserSession(
        id=2, username="visit", nome="Visitante Teste", perfil=PERFIL_VISITANTE_DB,
    ))
    @patch("services.devolucao_service.pode_editar_tratativa", return_value=True)
    def test_08_nf_permanece_inalterada(self, _mock_perm, _mock_user) -> None:
        dev_id = _inserir_devolucao_fixture(nf_nfd="1423312")
        antes_nf = _snapshot_devolucao(dev_id)["nf_nfd"]
        ok, _ = atualizar_tratativa(dev_id, "Aguardando retorno do cliente")
        self.assertTrue(ok)
        depois_nf = _snapshot_devolucao(dev_id)["nf_nfd"]
        self.assertEqual(depois_nf, antes_nf)

    @patch("services.devolucao_service.get_current_user", return_value=UserSession(
        id=2, username="visit", nome="Visitante Teste", perfil=PERFIL_VISITANTE_DB,
    ))
    @patch("services.devolucao_service.pode_editar_tratativa", return_value=True)
    def test_09_motivo_permanece_inalterado(self, _mock_perm, _mock_user) -> None:
        dev_id = _inserir_devolucao_fixture(motivo_devolucao="Entrega fora do prazo")
        antes_motivo = _snapshot_devolucao(dev_id)["motivo_devolucao"]
        ok, _ = atualizar_tratativa(dev_id, "Resolvido")
        self.assertTrue(ok)
        depois_motivo = _snapshot_devolucao(dev_id)["motivo_devolucao"]
        self.assertEqual(depois_motivo, antes_motivo)

    @patch("services.devolucao_service.get_current_user", return_value=UserSession(
        id=2, username="visit", nome="Visitante Teste", perfil=PERFIL_VISITANTE_DB,
    ))
    @patch("services.devolucao_service.pode_editar_tratativa", return_value=True)
    def test_10_demais_campos_permanecem_inalterados(self, _mock_perm, _mock_user) -> None:
        dev_id = _inserir_devolucao_fixture()
        antes = _snapshot_devolucao(dev_id)
        ok, _ = atualizar_tratativa(dev_id, "Concluído")
        self.assertTrue(ok)
        depois = _snapshot_devolucao(dev_id)
        self.assertNotEqual(depois["tratativa"], antes["tratativa"])
        self.assertEqual(depois["tratativa"], "Concluído")
        campos_imutaveis = [
            k
            for k in antes
            if k
            not in (
                "tratativa",
                "tratativa_atualizada_em",
                "tratativa_atualizada_por",
            )
        ]
        for campo in campos_imutaveis:
            self.assertEqual(depois[campo], antes[campo], campo)


class PermissaoTratativaTests(unittest.TestCase):
    @patch("core.permissions.get_current_user")
    def test_visitante_pode_editar_tratativa(self, mock_user) -> None:
        mock_user.return_value = UserSession(
            id=2,
            username="visit",
            nome="Visitante",
            perfil=PERFIL_VISITANTE_DB,
        )
        from core.permissions import pode_editar_tratativa

        self.assertTrue(pode_editar_tratativa())

    @patch("core.permissions.get_current_user")
    def test_admin_nao_pode_editar_tratativa(self, mock_user) -> None:
        mock_user.return_value = UserSession(
            id=1,
            username="admin",
            nome="Admin",
            perfil=PERFIL_ADMIN_DB,
        )
        from core.permissions import pode_editar_tratativa

        self.assertFalse(pode_editar_tratativa())


if __name__ == "__main__":
    unittest.main()
