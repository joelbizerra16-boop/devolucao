"""
Constantes e mapeamento de perfis — sem dependência de auth ou permissions.
"""

from __future__ import annotations

from database.models import PerfilUsuario

from core.tratativa_constants import (
    TRATATIVA_FILTRO_TODOS,
    TRATATIVA_FILTROS_UI,
    TRATATIVA_PADRAO,
)

LABEL_ADMIN = "ADMINISTRADOR"
LABEL_VISITANTE = "VISITANTE"

# Reexportação — preferir core.tratativa_constants em imports de UI

# Conta padrão do sistema — não pode ser editada nem excluída pela UI
USUARIO_PROTEGIDO = "admin"

PERFIS_COMBO = [LABEL_VISITANTE, LABEL_ADMIN]
PERFIS_VALIDOS = set(PERFIS_COMBO)

PERFIL_ADMIN_DB = PerfilUsuario.ADMIN.value
PERFIL_VISITANTE_DB = PerfilUsuario.VISUALIZADOR.value

PERFIL_LABELS = {
    LABEL_ADMIN: "Administrador",
    LABEL_VISITANTE: "Visitante",
}

MAPA_LABEL_PARA_DB = {
    LABEL_ADMIN: PerfilUsuario.ADMIN,
    LABEL_VISITANTE: PerfilUsuario.VISUALIZADOR,
}

MAPA_DB_PARA_LABEL = {
    PerfilUsuario.ADMIN.value: LABEL_ADMIN,
    PerfilUsuario.VISUALIZADOR.value: LABEL_VISITANTE,
    PerfilUsuario.OPERADOR.value: LABEL_VISITANTE,
    PerfilUsuario.SUPERVISOR.value: LABEL_VISITANTE,
}


def perfil_para_label(perfil_db: str) -> str:
    return MAPA_DB_PARA_LABEL.get(perfil_db, LABEL_VISITANTE)


def label_para_perfil(label: str) -> PerfilUsuario:
    return MAPA_LABEL_PARA_DB.get(label.strip().upper(), PerfilUsuario.VISUALIZADOR)
