"""
Autenticação e controle de sessão Streamlit.
Sessão em dict (serializável) para sobreviver a refresh da página.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import bcrypt
import streamlit as st

from core.constants import perfil_para_label
from core.database import PerfilUsuario, Usuario, get_session
from core.session_persistence import (
    clear_auth_cookie,
    create_auth_token,
    persist_auth_cookie,
    read_auth_token_from_request,
    store_auth_token,
    sync_auth_query_param,
    username_from_persistent_storage,
)

SESSION_AUTH_KEY = "authenticated"
SESSION_USER_KEY = "user"
SESSION_USERNAME_KEY = "auth_username"
SESSION_PERFIL_KEY = "perfil"
SESSION_EMPRESA_KEY = "empresa_id"


@dataclass
class UserSession:
    id: int
    username: str
    nome: str
    perfil: str
    empresa_id: Optional[int] = None

    def has_permission(self, required: PerfilUsuario | str) -> bool:
        hierarchy = {
            PerfilUsuario.VISUALIZADOR: 1,
            PerfilUsuario.OPERADOR: 2,
            PerfilUsuario.SUPERVISOR: 3,
            PerfilUsuario.ADMIN: 4,
        }
        user_level = hierarchy.get(PerfilUsuario(self.perfil), 0)
        req = required if isinstance(required, PerfilUsuario) else PerfilUsuario(required)
        return user_level >= hierarchy.get(req, 99)


def _usuario_para_dict(user: Usuario) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "nome": user.nome,
        "perfil": user.perfil.value,
        "empresa_id": user.empresa_id,
    }


def _dict_para_usuario(data: Any) -> Optional[UserSession]:
    if isinstance(data, UserSession):
        return data
    if not isinstance(data, dict):
        return None
    try:
        login = str(data.get("username") or data.get("usuario") or "").strip().lower()
        return UserSession(
            id=int(data["id"]),
            username=login,
            nome=str(data["nome"]),
            perfil=str(data["perfil"]),
            empresa_id=data.get("empresa_id"),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _aplicar_sessao(user: Usuario | dict[str, Any], *, persist_cookie: bool = True) -> None:
    dados = _usuario_para_dict(user) if isinstance(user, Usuario) else dict(user)
    st.session_state[SESSION_AUTH_KEY] = True
    st.session_state[SESSION_USER_KEY] = dados
    st.session_state[SESSION_USERNAME_KEY] = dados["username"]
    st.session_state[SESSION_PERFIL_KEY] = dados["perfil"]
    st.session_state[SESSION_EMPRESA_KEY] = dados.get("empresa_id")
    st.session_state["usuario"] = dados["username"]
    st.session_state["perfil"] = perfil_para_label(str(dados["perfil"]))
    if persist_cookie:
        persist_auth_cookie(str(dados["username"]))


def init_session_state() -> None:
    defaults = {
        SESSION_AUTH_KEY: False,
        SESSION_USER_KEY: None,
        SESSION_USERNAME_KEY: None,
        SESSION_PERFIL_KEY: None,
        SESSION_EMPRESA_KEY: None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    restore_session()


def _carregar_usuario_ativo(username: str) -> Optional[dict[str, Any]]:
    try:
        with get_session() as db:
            row = (
                db.query(Usuario)
                .filter(
                    Usuario.username == str(username).strip().lower(),
                    Usuario.ativo.is_(True),
                )
                .first()
            )
            if row is None:
                return None
            return _usuario_para_dict(row)
    except Exception:
        return None


def _tentar_restaurar_sessao() -> bool:
    """Recupera login a partir do session_state (rerun na mesma sessão Streamlit)."""
    if get_current_user() is not None:
        st.session_state[SESSION_AUTH_KEY] = True
        return True

    username = st.session_state.get(SESSION_USERNAME_KEY)
    if not username:
        return False

    dados = _carregar_usuario_ativo(str(username))
    if dados is None:
        return False
    _aplicar_sessao(dados, persist_cookie=False)
    return True


def _restaurar_persistente() -> bool:
    """Recupera login via ?auth=, cookie ou token salvo (F5 / refresh)."""
    username = username_from_persistent_storage()
    if not username:
        return False

    dados = _carregar_usuario_ativo(username)
    if dados is None:
        clear_auth_cookie()
        return False

    token = read_auth_token_from_request() or create_auth_token(dados["username"])
    store_auth_token(token)
    _aplicar_sessao(dados, persist_cookie=False)
    sync_auth_query_param()
    persist_auth_cookie(str(dados["username"]))
    return True


def restore_session() -> bool:
    """
    Restaura autenticação: session_state → URL/cookie.
    Deve ser chamado antes de exibir 'sessão expirada'.
    """
    if _tentar_restaurar_sessao():
        sync_auth_query_param()
        return True
    return _restaurar_persistente()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def login(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()
    if not username or not password:
        return False, "Informe usuário e senha."

    with get_session() as session:
        user = session.query(Usuario).filter(Usuario.username == username, Usuario.ativo.is_(True)).first()
        if not user or not verify_password(password, user.senha_hash):
            return False, "Credenciais inválidas."

        _aplicar_sessao(_usuario_para_dict(user))
        return True, f"Bem-vindo, {user.nome}!"


def logout() -> None:
    from core.navigation import clear_navigation_state

    clear_auth_cookie()
    clear_navigation_state()
    for key in [
        SESSION_AUTH_KEY,
        SESSION_USER_KEY,
        SESSION_USERNAME_KEY,
        SESSION_PERFIL_KEY,
        SESSION_EMPRESA_KEY,
    ]:
        st.session_state.pop(key, None)
    st.session_state[SESSION_AUTH_KEY] = False
    st.session_state.pop("usuario", None)
    st.session_state.pop("perfil", None)
    st.session_state.pop("_page_config_done", None)
    st.session_state.pop("_redirect_count", None)


def is_authenticated() -> bool:
    init_session_state()
    return get_current_user() is not None


def get_current_user() -> Optional[UserSession]:
    return _dict_para_usuario(st.session_state.get(SESSION_USER_KEY))


def require_auth(min_perfil: Optional[PerfilUsuario] = None) -> UserSession:
    """Exige autenticação; restaura sessão automaticamente após refresh."""
    init_session_state()

    user = get_current_user()
    if user is None and not restore_session():
        st.warning("Sessão expirada. Faça login novamente.")
        if st.button("Ir para o login", type="primary", use_container_width=True):
            st.switch_page("app.py")
        st.stop()

    user = get_current_user()
    if user is None:
        st.stop()

    if min_perfil and not user.has_permission(min_perfil):
        st.error("Você não tem permissão para acessar este recurso.")
        st.stop()

    return user
