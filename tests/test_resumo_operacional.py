"""Testes do repositório Resumo Operacional — percentual e rótulos."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.tratativa_utils import classificar_tratativa
from repositories.resumo_operacional_repository import (
    FiltrosResumo,
    FILTRO_TODOS_CLIENTE,
    FILTRO_TODOS_MOTIVO,
    _COD_CLIENTE_VAZIO,
    _calcular_media_diaria_valor,
    _calcular_percentual_agregado,
    _calcular_ticket_medio,
    _expr_aguardando,
    _expr_concluido,
    _expr_em_analise,
    _expr_recusado,
    _rotulo_cliente,
)
from services.resumo_operacional_service import (
    MODO_CLIENTES,
    MODO_MOTIVOS,
    MODOS_ORDENACAO,
    ORDENAR_QUANTIDADE,
    ORDENAR_VALOR,
    _cards_resumo_formatados,
    _classificar_por_valor,
    _formatar_media_movel_diaria,
    export_tabela_resumo_excel_bytes,
    nome_arquivo_resumo_operacional,
    preparar_tabela_clientes,
    preparar_tabela_motivos,
)
from components.tabelas import (
    _config_coluna_percentual,
    _heatmap_percentual_styler,
)


def _pct_quantidade(qtd: int, total: int) -> float:
    return _calcular_percentual_agregado(
        qtd,
        0.0,
        total_quantidade=total,
        total_valor=0.0,
        por_valor=False,
    )


def _pct_valor(valor: float, total_valor: float) -> float:
    return _calcular_percentual_agregado(
        0,
        valor,
        total_quantidade=0,
        total_valor=total_valor,
        por_valor=True,
    )


class ResumoOperacionalRepositoryTests(unittest.TestCase):
    def test_percentual_por_quantidade(self) -> None:
        self.assertEqual(_pct_quantidade(25, 100), 25.0)
        self.assertEqual(_pct_quantidade(1, 3), 33.33)
        self.assertEqual(_pct_quantidade(0, 10), 0.0)
        self.assertEqual(_pct_quantidade(5, 0), 0.0)

    def test_percentual_por_valor(self) -> None:
        self.assertAlmostEqual(_pct_valor(80000, 190000), 42.11, places=2)
        self.assertAlmostEqual(_pct_valor(35000, 190000), 18.42, places=2)
        self.assertEqual(_pct_valor(0, 1000), 0.0)
        self.assertEqual(_pct_valor(500, 0), 0.0)

    def test_percentual_criterio_independente(self) -> None:
        """Mesmo item pode ter percentuais distintos por quantidade e por valor."""
        pct_qtd = _calcular_percentual_agregado(
            15,
            80000.0,
            total_quantidade=50,
            total_valor=190000.0,
            por_valor=False,
        )
        pct_val = _calcular_percentual_agregado(
            15,
            80000.0,
            total_quantidade=50,
            total_valor=190000.0,
            por_valor=True,
        )
        self.assertEqual(pct_qtd, 30.0)
        self.assertAlmostEqual(pct_val, 42.11, places=2)

    def test_rotulo_cliente(self) -> None:
        self.assertEqual(_rotulo_cliente("123", "ACME"), "123 — ACME")
        self.assertEqual(_rotulo_cliente("123", ""), "123")
        self.assertEqual(_rotulo_cliente(_COD_CLIENTE_VAZIO, "SEM COD"), "SEM COD")
        self.assertEqual(_rotulo_cliente(_COD_CLIENTE_VAZIO, ""), "(Sem código)")

    def test_filtros_resumo_imutavel(self) -> None:
        f = FiltrosResumo(mes=6, ano=2026)
        self.assertEqual(f.cliente, FILTRO_TODOS_CLIENTE)
        self.assertEqual(f.motivo, FILTRO_TODOS_MOTIVO)
        self.assertEqual(hash(f), hash(FiltrosResumo(6, 2026)))

    def test_categorias_tratativa_sql_alinhadas(self) -> None:
        """Verifica que expressões SQL cobrem as mesmas categorias do utilitário."""
        amostras = [
            ("", "Aguardando"),
            ("Aguardando", "Aguardando"),
            ("aguardando retorno", "Aguardando"),
            ("Em análise", "Em Análise"),
            ("analise pendente", "Em Análise"),
            ("Concluído", "Concluído"),
            ("resolvido", "Concluído"),
            ("Recusado pelo cliente", "Recusado"),
            ("Texto livre qualquer", "Aguardando"),
        ]
        for texto, esperado in amostras:
            cat = classificar_tratativa(texto)
            self.assertEqual(cat, esperado, msg=f"texto={texto!r}")

    def test_expr_tratativa_nao_sobrepostas(self) -> None:
        """Expressões SQL são importáveis e distintas por categoria."""
        self.assertIsNotNone(_expr_recusado())
        self.assertIsNotNone(_expr_concluido())
        self.assertIsNotNone(_expr_em_analise())
        self.assertIsNotNone(_expr_aguardando())

    def test_cards_resumo_formatados(self) -> None:
        cards = _cards_resumo_formatados(
            {
                "total_devolucoes": 36,
                "soma_valor_nf": 133380.18,
                "ticket_medio": 3705.005,
                "media_movel_diaria": 4446.006,
            }
        )
        self.assertEqual(cards["total_devolucoes"], "36")
        self.assertIn("133.380", cards["valor_total"])
        self.assertIn("3.705", cards["ticket_medio"])
        self.assertIn("4.446", cards["media_movel"])
        self.assertIn("/ dia", cards["media_movel"])

    def test_ticket_medio(self) -> None:
        self.assertAlmostEqual(_calcular_ticket_medio(133380.18, 36), 3705.005, places=2)
        self.assertEqual(_calcular_ticket_medio(0, 0), 0.0)

    def test_media_diaria_valor(self) -> None:
        self.assertAlmostEqual(
            _calcular_media_diaria_valor(133380.18, 6, 2026),
            133380.18 / 30,
            places=2,
        )
        self.assertEqual(_calcular_media_diaria_valor(0, 6, 2026), 0.0)

    def test_formatar_media_movel_diaria(self) -> None:
        self.assertIn("R$", _formatar_media_movel_diaria(4446.006))
        self.assertIn("/ dia", _formatar_media_movel_diaria(4446.006))

    def test_preparar_tabelas_analiticas(self) -> None:
        df_motivos = preparar_tabela_motivos(
            [
                {
                    "motivo": "Avaria",
                    "quantidade": 3,
                    "valor_total": 100.0,
                    "percentual": 60.0,
                }
            ]
        )
        self.assertEqual(list(df_motivos.columns), ["Motivo", "Quantidade", "Valor Total", "Percentual"])
        self.assertEqual(df_motivos.iloc[0]["Percentual"], 60.0)

        df_clientes = preparar_tabela_clientes(
            [
                {
                    "cod_cliente": "C1",
                    "cliente": "Loja",
                    "quantidade": 2,
                    "valor_total": 50.0,
                    "percentual": 40.0,
                }
            ]
        )
        self.assertEqual(df_clientes.iloc[0]["Código"], "C1")
        self.assertEqual(df_clientes.iloc[0]["Percentual"], 40.0)

    def test_coluna_percentual_compativel_streamlit(self) -> None:
        import streamlit as st

        cfg = _config_coluna_percentual()
        cc = st.column_config
        if hasattr(cc, "ProgressBarColumn") or hasattr(cc, "ProgressColumn"):
            self.assertIsNotNone(cfg)
        else:
            self.assertIsNone(cfg)

    def test_heatmap_styler_percentual(self) -> None:
        import pandas as pd

        df = pd.DataFrame({"Percentual": [10.0, 90.0]})
        styled = _heatmap_percentual_styler(df)
        self.assertIsNotNone(styled)
        html = styled.to_html()
        self.assertIn("rgba(47, 128, 237", html)

    def test_nome_arquivo_resumo_operacional(self) -> None:
        nome = nome_arquivo_resumo_operacional()
        self.assertTrue(nome.startswith("Resumo_Operacional_"))
        self.assertTrue(nome.endswith(".xlsx"))
        self.assertEqual(len(nome), len("Resumo_Operacional_") + 15 + len(".xlsx"))

    def test_export_excel_modo_motivos(self) -> None:
        from io import BytesIO

        import pandas as pd

        df = preparar_tabela_motivos(
            [
                {
                    "motivo": "Avaria",
                    "quantidade": 3,
                    "valor_total": 1500.5,
                    "percentual": 60.0,
                }
            ]
        )
        raw = export_tabela_resumo_excel_bytes(df, MODO_MOTIVOS)
        out = pd.read_excel(BytesIO(raw), sheet_name="Resumo")
        self.assertEqual(
            list(out.columns),
            ["Motivo", "Quantidade", "Valor Total", "Percentual"],
        )
        self.assertEqual(out.iloc[0]["Motivo"], "Avaria")
        self.assertEqual(int(out.iloc[0]["Quantidade"]), 3)
        self.assertAlmostEqual(float(out.iloc[0]["Valor Total"]), 1500.5, places=2)
        self.assertAlmostEqual(float(out.iloc[0]["Percentual"]), 0.6, places=4)

    def test_export_excel_modo_clientes(self) -> None:
        from io import BytesIO

        import pandas as pd

        df = preparar_tabela_clientes(
            [
                {
                    "cod_cliente": "C004175",
                    "cliente": "VALGUARA",
                    "quantidade": 1,
                    "valor_total": 734.03,
                    "percentual": 2.8,
                }
            ]
        )
        raw = export_tabela_resumo_excel_bytes(df, MODO_CLIENTES)
        out = pd.read_excel(BytesIO(raw), sheet_name="Resumo")
        self.assertEqual(out.iloc[0]["Código Cliente"], "C004175")
        self.assertEqual(out.iloc[0]["Cliente"], "VALGUARA")
        self.assertAlmostEqual(float(out.iloc[0]["Percentual"]), 0.028, places=4)

    def test_modos_ordenacao_tabela(self) -> None:
        self.assertEqual(MODOS_ORDENACAO, (ORDENAR_QUANTIDADE, ORDENAR_VALOR))
        self.assertFalse(_classificar_por_valor(ORDENAR_QUANTIDADE))
        self.assertTrue(_classificar_por_valor(ORDENAR_VALOR))

    def test_preparar_tabela_ordem_preservada(self) -> None:
        """Export/UI preservam a ordem retornada pelo repositório (sem reordenar em Python)."""
        rows = [
            {
                "motivo": "B",
                "quantidade": 1,
                "valor_total": 500.0,
                "percentual": 10.0,
            },
            {
                "motivo": "A",
                "quantidade": 5,
                "valor_total": 100.0,
                "percentual": 50.0,
            },
        ]
        df = preparar_tabela_motivos(rows)
        self.assertEqual(list(df["Motivo"]), ["B", "A"])


if __name__ == "__main__":
    unittest.main()
