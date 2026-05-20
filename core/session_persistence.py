"""
Persistência de autenticação — sobrevive a F5.
Token assinado em ?auth= (principal) + cookie HTTP via script (backup).
Sem CookieManager em funções cacheadas (evita aviso de widget).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

COOKIE_NAME = "devolucao_auth"
AUTH_QUERY_KEY = "auth"
AUTH_TOKEN_SESSION_KEY = "_auth_token"
COOKIE_MAX_AGE_DAYS = 7
_AUTH_SECRET = os.environ.get(
    "DEVOLUCAO_AUTH_SECRET",
    "devolucao-wms-local-secret-altere-em-producao",
)


def _qp_value(key: str) -> Optional[str]:
    raw = st.query_params.get(key)
    if raw is None:
        return None
    if isinstance(raw, list):
        return str(raw[0]).strip() if raw else None
    return str(raw).strip() or None


def _sign(username: str, exp: int) -> str:
    payload = f"{username.lower()}|{exp}"
    sig = hmac.new(
        _AUTH_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    raw = f"{payload}|{sig}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def _verify(token: str) -> Optional[str]:
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        payload, sig = raw.rsplit("|", 1)
        username, exp_str = payload.split("|", 1)
        expected = hmac.new(
            _AUTH_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(exp_str) < int(time.time()):
            return None
        return username.lower()
    except Exception:
        return None


def create_auth_token(username: str) -> str:
    exp = int(time.time()) + COOKIE_MAX_AGE_DAYS * 86400
    return _sign(username.strip().lower(), exp)


def read_auth_token_from_request() -> Optional[str]:
    """Token na URL ou cookie HTTP da requisição (sem widgets)."""
    token = _qp_value(AUTH_QUERY_KEY)
    if token:
        return token

    token = st.session_state.get(AUTH_TOKEN_SESSION_KEY)
    if token:
        return str(token).strip()

    try:
        token = st.context.cookies.get(COOKIE_NAME)
        if token:
            return str(token).strip()
    except Exception:
        pass
    return None


def username_from_persistent_storage() -> Optional[str]:
    token = read_auth_token_from_request()
    if not token:
        return None
    return _verify(token)


def _inject_cookie_script(token: str, *, delete: bool = False) -> None:
    """Grava/remove cookie no navegador — só após login/logout, não no restore."""
    if st.session_state.get("_auth_cookie_script_done") == ("del" if delete else token):
        return

    max_age = 0 if delete else COOKIE_MAX_AGE_DAYS * 86400
    value_js = json.dumps("" if delete else token)
    components.html(
        f"""
        <script>
        (function() {{
            var v = {value_js};
            var c = "{COOKIE_NAME}=" + encodeURIComponent(v)
                + "; path=/; max-age={max_age}; SameSite=Lax";
            try {{
                window.parent.document.cookie = c;
            }} catch (e) {{
                document.cookie = c;
            }}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )
    st.session_state["_auth_cookie_script_done"] = "del" if delete else token


def store_auth_token(token: str) -> None:
    st.session_state[AUTH_TOKEN_SESSION_KEY] = token


def sync_auth_query_param() -> None:
    """Mantém ?auth= na URL para restaurar sessão após F5."""
    token = st.session_state.get(AUTH_TOKEN_SESSION_KEY)
    if not token:
        return
    if _qp_value(AUTH_QUERY_KEY) != token:
        st.query_params[AUTH_QUERY_KEY] = str(token)


def auth_query_params_extra() -> dict[str, str]:
    token = st.session_state.get(AUTH_TOKEN_SESSION_KEY) or _qp_value(AUTH_QUERY_KEY)
    if token:
        return {AUTH_QUERY_KEY: str(token)}
    return {}


def persist_auth_cookie(username: str) -> None:
    token = create_auth_token(username)
    if st.session_state.get(AUTH_TOKEN_SESSION_KEY) == token and st.session_state.get(
        "_auth_persisted"
    ):
        return

    store_auth_token(token)
    st.query_params[AUTH_QUERY_KEY] = token
    _inject_cookie_script(token)
    st.session_state["_auth_persisted"] = True


def clear_auth_cookie() -> None:
    st.session_state.pop(AUTH_TOKEN_SESSION_KEY, None)
    st.session_state.pop("_auth_persisted", None)
    st.session_state.pop("_auth_cookie_script_done", None)
    if AUTH_QUERY_KEY in st.query_params:
        del st.query_params[AUTH_QUERY_KEY]
    _inject_cookie_script("", delete=True)


def username_from_persistent_cookie() -> Optional[str]:
    return username_from_persistent_storage()
