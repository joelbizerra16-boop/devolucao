"""Testes de exportação — coluna TRATATIVA em Excel e PDF."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from services.dashboard_service import preparar_listview_dashboard
from services.export_dashboard_service import (
    _linhas_tabela_pdf,
    export_listagem_excel_bytes,
    export_listagem_pdf_bytes,
)


def _row(
    *,
    tratativa: str = "Aguardando",
    motivo: str = "Duplicidade de pedido",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        data_devolucao=date(2026, 6, 19),
        usuario="Douglas",
        usuario_ultima_edicao=None,
        motivo_devolucao=motivo,
        tratativa=tratativa,
        nf_nfd="1424371",
        valor_nf=59985.0,
        cod_cliente="C005319",
        vendedor="André Luis Da Silva",
    )


class TestExportTratativa(unittest.TestCase):
    def test_preparar_listview_inclui_tratativa_na_ordem(self) -> None:
        df = preparar_listview_dashboard([_row(tratativa="Aguardando")])
        self.assertEqual(
            list(df.columns),
            [
                "DATA + USUARIO",
                "MOTIVO",
                "TRATATIVA",
                "NF",
                "VALOR",
                "COD CLIENTE",
                "VENDEDOR",
            ],
        )
        self.assertEqual(df.iloc[0]["TRATATIVA"], "Aguardando")

    def test_tratativa_texto_longo_sem_truncamento(self) -> None:
        texto = "Cliente se enganou, pediu sim."
        df = preparar_listview_dashboard([_row(tratativa=texto)])
        self.assertEqual(df.iloc[0]["TRATATIVA"], texto)

    def test_tratativa_vazia_usa_padrao_aguardando(self) -> None:
        df = preparar_listview_dashboard([_row(tratativa="")])
        self.assertEqual(df.iloc[0]["TRATATIVA"], "Aguardando")

    def test_export_excel_bytes_contem_coluna_tratativa(self) -> None:
        rows = [
            _row(tratativa="Aguardando"),
            _row(
                tratativa="Pedido errado - cliente pediu outro produto.",
                motivo="Pedido errado",
            ),
        ]
        raw = export_listagem_excel_bytes(rows)
        df = pd.read_excel(BytesIO(raw), sheet_name="Listagem")
        self.assertIn("TRATATIVA", df.columns.tolist())
        self.assertEqual(df.iloc[0]["TRATATIVA"], "Aguardando")
        self.assertEqual(
            df.iloc[1]["TRATATIVA"],
            "Pedido errado - cliente pediu outro produto.",
        )

    def test_linhas_pdf_incluem_tratativa(self) -> None:
        linhas = _linhas_tabela_pdf(
            [_row(tratativa="Entrega fora do prazo.")]
        )
        self.assertEqual(len(linhas[0]), 8)
        self.assertEqual(linhas[0][3], "Entrega fora do prazo.")

    def test_export_pdf_bytes_gera_arquivo(self) -> None:
        raw = export_listagem_pdf_bytes(
            [_row(tratativa="Aguardando")],
            mes="Junho",
            ano=2026,
        )
        self.assertTrue(raw.startswith(b"%PDF"))
        self.assertGreater(len(raw), 500)


if __name__ == "__main__":
    unittest.main()
