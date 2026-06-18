"""Testes do modal Editar Tratativa — estado do campo e helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _SessionState(dict):
    def get(self, key, default=None):
        return super().get(key, default)

    def pop(self, key, default=None):
        return super().pop(key, default)


class TratativaModalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session_state = _SessionState()

    @patch("components.listagem_dashboard.st")
    def test_prepare_field_inicializa_uma_vez_por_abertura(self, mock_st) -> None:
        mock_st.session_state = self.session_state
        from components.listagem_dashboard import _prepare_tratativa_field, _tratativa_field_key

        key = _prepare_tratativa_field(42, "Aguardando")
        self.assertEqual(key, _tratativa_field_key(42))
        self.assertEqual(self.session_state[key], "Aguardando")
        self.assertEqual(self.session_state["dash_tratativa_open_id"], 42)

        self.session_state[key] = "Texto editado pelo usuário"
        key2 = _prepare_tratativa_field(42, "Aguardando")
        self.assertEqual(key, key2)
        self.assertEqual(self.session_state[key], "Texto editado pelo usuário")

    @patch("components.listagem_dashboard.st")
    def test_prepare_field_reinicializa_ao_trocar_registro(self, mock_st) -> None:
        mock_st.session_state = self.session_state
        from components.listagem_dashboard import _prepare_tratativa_field, _tratativa_field_key

        _prepare_tratativa_field(1, "Aguardando")
        _prepare_tratativa_field(2, "Em análise")
        self.assertEqual(self.session_state[_tratativa_field_key(2)], "Em análise")
        self.assertEqual(self.session_state["dash_tratativa_open_id"], 2)

    @patch("components.listagem_dashboard.st")
    def test_fechar_modal_limpa_estado(self, mock_st) -> None:
        mock_st.session_state = self.session_state
        from components.listagem_dashboard import (
            _fechar_modal_tratativa,
            _prepare_tratativa_field,
            _tratativa_field_key,
        )

        _prepare_tratativa_field(9, "Concluído")
        self.session_state["dash_tratativa_id"] = 9
        _fechar_modal_tratativa(9)
        self.assertNotIn("dash_tratativa_id", self.session_state)
        self.assertNotIn("dash_tratativa_open_id", self.session_state)
        self.assertNotIn(_tratativa_field_key(9), self.session_state)


if __name__ == "__main__":
    unittest.main()
