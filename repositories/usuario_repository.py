"""Repositório — usuários do sistema."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from core.database import PerfilUsuario, Usuario
from core.db import get_session, get_write_session
# Coluna real no PostgreSQL/Supabase: username (Usuario.usuario e synonym legado)
_LOGIN_COL = Usuario.username


def _usuario_para_dict(row: Usuario) -> dict:
    return {
        "id": int(row.id),
        "nome": row.nome,
        "username": row.username,
        "senha_hash": row.senha_hash,
        "perfil": row.perfil.value if hasattr(row.perfil, "value") else str(row.perfil),
        "ativo": bool(row.ativo),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if getattr(row, "updated_at", None) else None,
        "empresa_id": getattr(row, "empresa_id", None),
    }


def listar_todos() -> list[dict]:
    with get_session() as session:
        rows = session.query(Usuario).order_by(Usuario.nome.asc()).all()
        return [_usuario_para_dict(r) for r in rows]


def buscar_por_id(usuario_id: int) -> Optional[Usuario]:
    with get_session() as session:
        return session.get(Usuario, usuario_id)


def contar_admins(apenas_ativos: bool = True) -> int:
    with get_session() as session:
        q = session.query(Usuario).filter(Usuario.perfil == PerfilUsuario.ADMIN)
        if apenas_ativos:
            q = q.filter(Usuario.ativo.is_(True))
        return q.count()


def buscar_por_username(username: str) -> Optional[Usuario]:
    chave = username.strip().lower()
    if not chave:
        return None
    with get_session() as session:
        return session.query(Usuario).filter(_LOGIN_COL == chave).first()


def username_existe(username: str, ignorar_id: Optional[int] = None) -> bool:
    chave = username.strip().lower()
    if not chave:
        return False
    with get_session() as session:
        q = session.query(Usuario.id).filter(_LOGIN_COL == chave)
        if ignorar_id is not None:
            q = q.filter(Usuario.id != ignorar_id)
        return q.first() is not None


def inserir(
    nome: str,
    username: str,
    senha_hash: str,
    perfil: PerfilUsuario,
    ativo: bool = True,
) -> int:
    with get_write_session() as session:
        user = Usuario(
            nome=nome.strip(),
            username=username.strip().lower(),
            senha_hash=senha_hash,
            perfil=perfil,
            ativo=ativo,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(user)
        session.flush()
        return user.id


def atualizar(
    usuario_id: int,
    nome: str,
    perfil: PerfilUsuario,
    senha_hash: Optional[str] = None,
) -> bool:
    with get_write_session() as session:
        user = session.get(Usuario, usuario_id)
        if user is None:
            return False
        user.nome = nome.strip()
        user.perfil = perfil
        if senha_hash:
            user.senha_hash = senha_hash
        user.updated_at = datetime.utcnow()
        return True


def excluir(usuario_id: int) -> bool:
    with get_write_session() as session:
        user = session.get(Usuario, usuario_id)
        if user is None:
            return False
        session.delete(user)
        return True


def alternar_ativo(usuario_id: int) -> Optional[bool]:
    """Retorna novo estado ativo ou None se usuário não existe."""
    with get_write_session() as session:
        user = session.get(Usuario, usuario_id)
        if user is None:
            return None
        user.ativo = not user.ativo
        user.updated_at = datetime.utcnow()
        return user.ativo
