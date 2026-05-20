"""Serviço de usuários — cadastro, listagem e seed."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any, Optional

import pandas as pd
import streamlit as st

from core.auth import hash_password
from core.cache_read import TTL_USUARIOS, limpar_cache_leitura
from core.database import PerfilUsuario, init_db
from core.constants import (
    PERFIS_VALIDOS,
    USUARIO_PROTEGIDO,
    label_para_perfil,
    perfil_para_label,
)
from repositories import usuario_repository


def get_user_by_username(username: str):
    return usuario_repository.buscar_por_username(username)


def seed_default_users() -> None:
    """Cria usuário administrador padrão se não existir."""
    init_db()
    if usuario_repository.buscar_por_username(USUARIO_PROTEGIDO):
        return
    usuario_repository.inserir(
        nome="Administrador",
        username=USUARIO_PROTEGIDO,
        senha_hash=hash_password("admin123"),
        perfil=PerfilUsuario.ADMIN,
    )


def _fmt_data(valor: Optional[datetime]) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    return str(valor)


def _serializar_usuario(row: Any) -> dict[str, Any]:
    created = row.created_at
    if isinstance(created, datetime):
        created = created.isoformat()
    perfil = row.perfil.value if hasattr(row.perfil, "value") else str(row.perfil)
    return {
        "id": int(row.id),
        "nome": row.nome,
        "username": row.username,
        "perfil": perfil,
        "ativo": bool(row.ativo),
        "created_at": created,
    }


def _deserializar_usuario(dados: dict[str, Any]) -> SimpleNamespace:
    from core.database import PerfilUsuario

    created = dados.get("created_at")
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created)
        except ValueError:
            created = None
    try:
        perfil = PerfilUsuario(dados["perfil"])
    except (ValueError, KeyError):
        perfil = SimpleNamespace(value=dados.get("perfil"))
    return SimpleNamespace(
        id=dados["id"],
        nome=dados.get("nome"),
        username=dados.get("username"),
        perfil=perfil,
        ativo=dados.get("ativo", True),
        created_at=created,
    )


@st.cache_data(ttl=TTL_USUARIOS, show_spinner=False)
def listar_usuarios_cache() -> tuple[dict[str, Any], ...]:
    rows = usuario_repository.listar_todos()
    return tuple(_serializar_usuario(r) for r in rows)


def listar_usuarios() -> list:
    """Lista entidades Usuario ordenadas por nome."""
    return [_deserializar_usuario(d) for d in listar_usuarios_cache()]


def buscar_usuario_por_id(usuario_id: int):
    return usuario_repository.buscar_por_id(usuario_id)


def usuario_e_protegido(usuario) -> bool:
    """Conta padrão do sistema (admin) — bloqueada para edição e exclusão."""
    if usuario is None:
        return False
    return (usuario.username or "").strip().lower() == USUARIO_PROTEGIDO


def usuario_pode_ser_editado(usuario_id: int) -> bool:
    alvo = usuario_repository.buscar_por_id(usuario_id)
    return alvo is not None and not usuario_e_protegido(alvo)


@st.cache_data(ttl=TTL_USUARIOS, show_spinner=False)
def listar_usuarios_df_cache() -> pd.DataFrame:
    rows = listar_usuarios()
    colunas = ["Nome", "Usuário", "Perfil", "Status", "Data criação"]
    if not rows:
        return pd.DataFrame(columns=colunas)

    dados = [
        {
            "Nome": r.nome,
            "Usuário": r.username,
            "Perfil": perfil_para_label(r.perfil.value),
            "Status": "Ativo" if r.ativo else "Inativo",
            "Data criação": _fmt_data(r.created_at),
        }
        for r in rows
    ]
    return pd.DataFrame(dados, columns=colunas)


def listar_usuarios_df() -> pd.DataFrame:
    return listar_usuarios_df_cache()


def cadastrar_usuario(
    nome: str,
    usuario: str,
    perfil_label: str,
    senha: str,
) -> tuple[bool, str]:
    nome_txt = (nome or "").strip()
    usuario_txt = (usuario or "").strip().lower()
    senha_txt = (senha or "").strip()
    perfil_norm = (perfil_label or "").strip().upper()

    if not nome_txt:
        return False, "Informe o nome."
    if not usuario_txt:
        return False, "Informe o usuário."
    if not senha_txt:
        return False, "Informe a senha."
    if perfil_norm not in PERFIS_VALIDOS:
        return False, "Perfil inválido. Use VISITANTE ou ADMINISTRADOR."

    if usuario_repository.username_existe(usuario_txt):
        return False, f"O usuário «{usuario_txt}» já está cadastrado."

    try:
        perfil_db = label_para_perfil(perfil_norm)
        usuario_repository.inserir(
            nome=nome_txt,
            username=usuario_txt,
            senha_hash=hash_password(senha_txt),
            perfil=perfil_db,
        )
        limpar_cache_leitura()
        return True, "Usuário cadastrado com sucesso."
    except Exception as exc:
        return False, f"Erro ao cadastrar usuário: {exc}"


def atualizar_usuario(
    usuario_id: int,
    nome: str,
    perfil_label: str,
    senha: str = "",
) -> tuple[bool, str]:
    nome_txt = (nome or "").strip()
    senha_txt = (senha or "").strip()
    perfil_norm = (perfil_label or "").strip().upper()

    if not nome_txt:
        return False, "Informe o nome."
    if perfil_norm not in PERFIS_VALIDOS:
        return False, "Perfil inválido. Use VISITANTE ou ADMINISTRADOR."

    existente = usuario_repository.buscar_por_id(usuario_id)
    if existente is None:
        return False, "Usuário não encontrado."
    if usuario_e_protegido(existente):
        return False, "O usuário administrador padrão não pode ser editado."

    try:
        perfil_db = label_para_perfil(perfil_norm)
        senha_hash = hash_password(senha_txt) if senha_txt else None
        ok = usuario_repository.atualizar(
            usuario_id=usuario_id,
            nome=nome_txt,
            perfil=perfil_db,
            senha_hash=senha_hash,
        )
        if not ok:
            return False, "Usuário não encontrado."
        limpar_cache_leitura()
        return True, "Usuário atualizado com sucesso."
    except Exception as exc:
        return False, f"Erro ao atualizar usuário: {exc}"


def excluir_usuario(usuario_id: int, usuario_logado_id: int) -> tuple[bool, str]:
    if usuario_id == usuario_logado_id:
        return False, "Não é permitido excluir o próprio usuário."

    alvo = usuario_repository.buscar_por_id(usuario_id)
    if alvo is None:
        return False, "Usuário não encontrado."
    if usuario_e_protegido(alvo):
        return False, "O usuário administrador padrão não pode ser excluído."

    if alvo.perfil == PerfilUsuario.ADMIN and usuario_repository.contar_admins() <= 1:
        return False, "Deve existir ao menos um administrador."

    try:
        if not usuario_repository.excluir(usuario_id):
            return False, "Usuário não encontrado."
        limpar_cache_leitura()
        return True, "Usuário excluído com sucesso."
    except Exception as exc:
        return False, f"Erro ao excluir usuário: {exc}"


def alternar_status_usuario(usuario_id: int) -> tuple[bool, str]:
    existente = usuario_repository.buscar_por_id(usuario_id)
    if existente is None:
        return False, "Usuário não encontrado."
    if usuario_e_protegido(existente):
        return False, "O usuário administrador padrão não pode ser desativado."
    if existente.perfil == PerfilUsuario.ADMIN and existente.ativo:
        if usuario_repository.contar_admins(apenas_ativos=True) <= 1:
            return False, "Deve existir ao menos um administrador ativo."
    try:
        novo = usuario_repository.alternar_ativo(usuario_id)
        if novo is None:
            return False, "Usuário não encontrado."
        estado = "ativado" if novo else "desativado"
        limpar_cache_leitura()
        return True, f"Usuário {estado} com sucesso."
    except Exception as exc:
        return False, f"Erro ao alterar status: {exc}"


def create_user(
    username: str,
    password: str,
    nome: str,
    perfil: PerfilUsuario = PerfilUsuario.VISUALIZADOR,
    email: Optional[str] = None,
    empresa_id: Optional[int] = None,
):
    """Compatibilidade — preferir cadastrar_usuario."""
    return usuario_repository.inserir(
        nome=nome,
        username=username,
        senha_hash=hash_password(password),
        perfil=perfil,
    )
