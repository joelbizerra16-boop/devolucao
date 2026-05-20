"""
Cache de leitura Streamlit — TTLs e invalidação centralizada.

Aplicar apenas em consultas (SELECT). Após INSERT/UPDATE/DELETE, chamar limpar_cache_leitura().
"""

from __future__ import annotations

# TTLs em segundos
TTL_DASHBOARD = 300
TTL_DEVOLUCOES = 300
TTL_SAP = 300
TTL_USUARIOS = 300
TTL_MOTIVOS = 600


def limpar_cache_leitura() -> None:
    """Invalida todos os caches de leitura após alterações no banco."""
    from services import dashboard_service, devolucao_service, motivo_service, sap_service
    from services import usuario_service

    funcoes = (
        dashboard_service.carregar_dashboard,
        dashboard_service.carregar_listview_dashboard,
        dashboard_service.obter_graficos_cache,
        dashboard_service.obter_anos_disponiveis_cache,
        dashboard_service.obter_periodo_padrao_cache,
        dashboard_service.listar_devolucoes_periodo_cache,
        devolucao_service.listar_devolucoes_cache,
        devolucao_service.obter_metricas_cards_cache,
        motivo_service.listar_motivos_cache,
        motivo_service.listar_motivos_df_cache,
        sap_service.buscar_nf_cache,
        sap_service.contar_base_cache,
        sap_service.obter_arquivo_ativo_cache,
        usuario_service.listar_usuarios_cache,
        usuario_service.listar_usuarios_df_cache,
    )

    for func in funcoes:
        if hasattr(func, "clear"):
            func.clear()
