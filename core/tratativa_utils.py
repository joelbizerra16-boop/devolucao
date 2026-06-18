"""Classificação e filtro de tratativas — sem dependência de UI."""

from __future__ import annotations

from core.tratativa_constants import TRATATIVA_FILTRO_TODOS, TRATATIVA_FILTROS_UI, TRATATIVA_PADRAO

CATEGORIA_AGUARDANDO = "Aguardando"
CATEGORIA_EM_ANALISE = "Em Análise"
CATEGORIA_CONCLUIDO = "Concluído"
CATEGORIA_RECUSADO = "Recusado"

CATEGORIAS_TRATATIVA = [
    CATEGORIA_AGUARDANDO,
    CATEGORIA_EM_ANALISE,
    CATEGORIA_CONCLUIDO,
    CATEGORIA_RECUSADO,
]


def classificar_tratativa(texto: str | None) -> str:
    """Mapeia texto livre da tratativa para uma categoria de indicador/filtro."""
    t = (texto or "").strip().lower()
    if not t:
        return CATEGORIA_AGUARDANDO
    if "recusad" in t:
        return CATEGORIA_RECUSADO
    if "conclu" in t or t == "resolvido":
        return CATEGORIA_CONCLUIDO
    if "análise" in t or "analise" in t:
        return CATEGORIA_EM_ANALISE
    if t == TRATATIVA_PADRAO.lower() or t.startswith("aguardando"):
        return CATEGORIA_AGUARDANDO
    return CATEGORIA_AGUARDANDO


def tratativa_corresponde_filtro(tratativa: str | None, filtro: str) -> bool:
    if not filtro or filtro == TRATATIVA_FILTRO_TODOS:
        return True
    return classificar_tratativa(tratativa) == filtro.strip()


def filtrar_linhas_por_tratativa(rows: list, filtro: str) -> list:
    if not filtro or filtro == TRATATIVA_FILTRO_TODOS:
        return list(rows)
    resultado = []
    for row in rows:
        valor = row.get("tratativa") if isinstance(row, dict) else getattr(row, "tratativa", None)
        if tratativa_corresponde_filtro(valor, filtro):
            resultado.append(row)
    return resultado


def eh_tratativa_aguardando(texto: str | None) -> bool:
    """KPI do dashboard — somente valor exato do status parametrizado (TRATATIVA_PADRAO)."""
    if texto is None:
        return True
    t = str(texto).strip()
    if not t:
        return True
    return t.casefold() == TRATATIVA_PADRAO.casefold()


def contar_aguardando_kpi(tratativas: list[str | None]) -> int:
    return sum(1 for t in tratativas if eh_tratativa_aguardando(t))


def calcular_pct_analisada(total: int, aguardando: int) -> float:
    """Percentual analisado: (DEVOLUÇÕES - AGUARDANDO) / DEVOLUÇÕES × 100."""
    total_int = int(total)
    aguardando_int = int(aguardando)
    if total_int <= 0:
        return 0.0
    analisadas = total_int - aguardando_int
    if analisadas + aguardando_int != total_int:
        from core.system_log import log_event

        log_event(
            "kpi",
            f"Inconsistência KPI tratativa: total={total_int} aguardando={aguardando_int} "
            f"analisadas={analisadas}",
        )
    return round(max(0, analisadas) / total_int * 100, 2)


def calcular_kpi_tratativa_dashboard(tratativas: list[str | None]) -> dict[str, int | float]:
    """Aguardando (exato) + % analisada para cards superiores do dashboard."""
    total = len(tratativas)
    aguardando = contar_aguardando_kpi(tratativas)
    analisadas = total - aguardando
    if analisadas + aguardando != total:
        from core.system_log import log_event

        log_event(
            "kpi",
            f"Inconsistência KPI tratativa: total={total} aguardando={aguardando} "
            f"analisadas={analisadas}",
        )
    pct = calcular_pct_analisada(total, aguardando)
    return {
        "total_aguardando": aguardando,
        "total_analisadas": analisadas,
        "pct_analisada": pct,
    }


def formatar_pct_analisada(pct: float) -> str:
    return f"{float(pct):.2f}".replace(".", ",") + "%"


def calcular_indicadores_tratativa(rows: list) -> dict[str, int]:
    """Contagens por categoria a partir das linhas já filtradas (sem consulta extra)."""
    contagem = {cat: 0 for cat in CATEGORIAS_TRATATIVA}
    for row in rows:
        valor = row.get("tratativa") if isinstance(row, dict) else getattr(row, "tratativa", None)
        cat = classificar_tratativa(valor)
        contagem[cat] = contagem.get(cat, 0) + 1
    return {
        "total_devolucoes": len(rows),
        "total_aguardando": contagem[CATEGORIA_AGUARDANDO],
        "total_em_analise": contagem[CATEGORIA_EM_ANALISE],
        "total_concluido": contagem[CATEGORIA_CONCLUIDO],
        "total_recusado": contagem[CATEGORIA_RECUSADO],
    }


__all__ = [
    "TRATATIVA_FILTRO_TODOS",
    "TRATATIVA_FILTROS_UI",
    "CATEGORIAS_TRATATIVA",
    "classificar_tratativa",
    "tratativa_corresponde_filtro",
    "filtrar_linhas_por_tratativa",
    "calcular_indicadores_tratativa",
    "calcular_pct_analisada",
    "calcular_kpi_tratativa_dashboard",
    "contar_aguardando_kpi",
    "eh_tratativa_aguardando",
    "formatar_pct_analisada",
]
