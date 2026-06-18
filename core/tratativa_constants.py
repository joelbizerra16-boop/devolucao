"""Constantes de tratativa — sem dependência de ORM ou banco."""

from __future__ import annotations

TRATATIVA_PADRAO = "Aguardando"

TRATATIVA_FILTRO_TODOS = "Todos"
TRATATIVA_FILTROS_UI = [
    TRATATIVA_FILTRO_TODOS,
    "Aguardando",
    "Em Análise",
    "Concluído",
    "Recusado",
]
