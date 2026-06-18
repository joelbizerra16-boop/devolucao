"""Testes do KPI % Analisada — regra oficial do dashboard."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.tratativa_utils import (
    calcular_kpi_tratativa_dashboard,
    calcular_pct_analisada,
    contar_aguardando_kpi,
    eh_tratativa_aguardando,
    formatar_pct_analisada,
)
from services.dashboard_service import _cards_formatados


class KpiAnalisadaTests(unittest.TestCase):
    def test_aguardando_somente_valor_exato(self) -> None:
        self.assertTrue(eh_tratativa_aguardando("Aguardando"))
        self.assertTrue(eh_tratativa_aguardando("aguardando"))
        self.assertFalse(eh_tratativa_aguardando("Cliente se enganou, pediu sim."))
        self.assertFalse(eh_tratativa_aguardando("Em análise"))
        self.assertFalse(eh_tratativa_aguardando("Aguardando retorno do cliente"))

    def test_cenario_1_todas_aguardando(self) -> None:
        tratativas = ["Aguardando"] * 57
        aguardando = contar_aguardando_kpi(tratativas)
        self.assertEqual(aguardando, 57)
        pct = calcular_pct_analisada(57, aguardando)
        self.assertEqual(pct, 0.0)
        self.assertEqual(formatar_pct_analisada(pct), "0,00%")
        kpi = calcular_kpi_tratativa_dashboard(tratativas)
        self.assertEqual(kpi["total_analisadas"], 0)
        cards = _cards_formatados(
            {
                "soma_valor_nf": 0,
                "total_devolucoes": 57,
                "total_aguardando": kpi["total_aguardando"],
                "pct_analisada": kpi["pct_analisada"],
                "principal_motivo": None,
                "principal_motivo_qtd": 0,
            }
        )
        self.assertEqual(cards["pct_analisada"], "0,00%")

    def test_cenario_2_parcialmente_analisadas(self) -> None:
        tratativas = ["Aguardando"] * 20 + ["Em análise"] * 37
        aguardando = contar_aguardando_kpi(tratativas)
        self.assertEqual(aguardando, 20)
        pct = calcular_pct_analisada(57, aguardando)
        self.assertAlmostEqual(pct, 64.91, places=2)
        self.assertEqual(formatar_pct_analisada(pct), "64,91%")
        kpi = calcular_kpi_tratativa_dashboard(tratativas)
        self.assertEqual(kpi["total_analisadas"], 37)
        self.assertEqual(kpi["total_aguardando"] + kpi["total_analisadas"], 57)

    def test_cenario_3_todas_analisadas(self) -> None:
        tratativas = ["Concluído"] * 57
        aguardando = contar_aguardando_kpi(tratativas)
        self.assertEqual(aguardando, 0)
        pct = calcular_pct_analisada(57, aguardando)
        self.assertEqual(pct, 100.0)
        self.assertEqual(formatar_pct_analisada(pct), "100,00%")

    def test_texto_livre_conta_como_analisada(self) -> None:
        """Registro da listagem com tratativa customizada não é Aguardando exato."""
        tratativas = ["Aguardando"] * 56 + ["Cliente se enganou, pediu sim."]
        kpi = calcular_kpi_tratativa_dashboard(tratativas)
        self.assertEqual(kpi["total_aguardando"], 56)
        self.assertEqual(kpi["total_analisadas"], 1)
        self.assertAlmostEqual(float(kpi["pct_analisada"]), round(1 / 57 * 100, 2), places=2)


if __name__ == "__main__":
    unittest.main()
