"""Listagem operacional do dashboard — visual premium com ações em ícones."""

from __future__ import annotations

from datetime import date
from html import escape
from typing import Callable

import streamlit as st

from core.auth import get_current_user
from core.permissions import pode_editar
from core.styles import inject_listview_premium_css
from core.theme import LISTVIEW_PAGE_SIZE, LISTVIEW_SCROLL_PX
from repositories import devolucao_repository
from services.csv_repository import listar_motivos
from core.cache_read import limpar_cache_leitura
from services.devolucao_service import (
    _formatar_data,
    _formatar_valor_br,
    _nome_responsavel_exibicao,
    _texto_celula,
    atualizar_devolucao,
    excluir_devolucao,
)

# Proporções fixas (soma 7.55) — alinhadas ao CSS grid em core/styles.py
_COLS_DADOS = [0.8, 2.1, 0.8, 0.9, 1.0, 1.4]
_COLS_ACOES = 0.55
_COLS_HEADER = [*_COLS_DADOS, _COLS_ACOES]
_COLS_ROW = _COLS_HEADER

_ICON_EDITAR = ":material/edit:"
_ICON_EXCLUIR = ":material/delete:"


def _linha_para_exibicao(row) -> dict[str, str]:
    data_txt = _formatar_data(row.data_devolucao)
    usuario = _nome_responsavel_exibicao(row)
    return {
        "data_txt": data_txt,
        "usuario": usuario,
        "motivo": _texto_celula(row.motivo_devolucao),
        "nf": _texto_celula(row.nf_nfd),
        "valor": _formatar_valor_br(row.valor_nf),
        "cod_cliente": _texto_celula(row.cod_cliente),
        "vendedor": _texto_celula(row.vendedor),
    }


def _html_celula_usuario(data_txt: str, usuario: str) -> str:
    return (
        f'<div class="lv-cell lv-cell-user">'
        f'<span class="lv-meta-row">'
        f'<span class="lv-meta-icon">◷</span>'
        f'<span class="lv-date">{escape(data_txt)}</span>'
        f"</span>"
        f'<span class="lv-meta-row lv-meta-row-user">'
        f'<span class="lv-meta-icon">◦</span>'
        f'<span class="lv-name" title="{escape(usuario, quote=True)}">{escape(usuario)}</span>'
        f"</span>"
        f"</div>"
    )


def _html_celula(
    texto: str,
    *,
    valor: bool = False,
    extra_class: str = "",
    title: str | None = None,
) -> str:
    classes = ["lv-cell"]
    if valor:
        classes.append("lv-cell-valor")
    if extra_class:
        classes.append(extra_class)
    title_attr = f' title="{escape(title, quote=True)}"' if title else ""
    return f'<p class="{" ".join(classes)}"{title_attr}>{escape(texto)}</p>'


def _html_badge(texto: str, *, extra_class: str = "", title: str | None = None) -> str:
    classes = ["lv-badge"]
    if extra_class:
        classes.append(extra_class)
    title_attr = f' title="{escape(title, quote=True)}"' if title else ""
    return f'<span class="{" ".join(classes)}"{title_attr}>{escape(texto)}</span>'


@st.dialog("Editar devolução")
def _dialog_editar(devolucao_id: int) -> None:
    dev = devolucao_repository.obter_por_id(devolucao_id)
    if dev is None:
        st.error("Registro não encontrado.")
        if st.button("Fechar"):
            st.session_state.pop("dash_edit_id", None)
            st.rerun()
        return

    user = get_current_user()
    editor = user.nome if user else ""
    motivos = listar_motivos()
    if not motivos:
        st.warning("Cadastre motivos em Configuração Motivos.")
        return

    st.caption(f"NF atual: **{dev.nf_nfd or '—'}**")
    with st.form("form_editar_devolucao"):
        data_dev = st.date_input(
            "D. DEVOLUÇÃO",
            value=dev.data_devolucao or date.today(),
            format="DD/MM/YYYY",
        )
        nf_nfd = st.text_input("NF/NFD", value=dev.nf_nfd or "")
        idx_motivo = 0
        if dev.motivo_devolucao in motivos:
            idx_motivo = motivos.index(dev.motivo_devolucao)
        motivo = st.selectbox("MOTIVO", options=motivos, index=idx_motivo)
        c1, c2 = st.columns(2)
        with c1:
            salvar = st.form_submit_button("Salvar", type="primary", use_container_width=True)
        with c2:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

    if cancelar:
        st.session_state.pop("dash_edit_id", None)
        st.rerun()

    if salvar:
        ok, msg = atualizar_devolucao(
            devolucao_id,
            data_devolucao=data_dev,
            nf_nfd=nf_nfd,
            motivo_devolucao=motivo,
            editor=editor,
        )
        if ok:
            st.session_state.pop("dash_edit_id", None)
            limpar_cache_leitura()
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)


@st.dialog("Excluir devolução")
def _dialog_excluir(devolucao_id: int) -> None:
    dev = devolucao_repository.obter_por_id(devolucao_id)
    if dev is None:
        st.error("Registro não encontrado.")
        st.session_state.pop("dash_del_id", None)
        st.rerun()
        return

    st.warning(
        f"Confirma a exclusão da NF **{_texto_celula(dev.nf_nfd)}** "
        f"({_formatar_data(dev.data_devolucao)})?"
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Confirmar exclusão", type="primary", use_container_width=True):
            ok, msg = excluir_devolucao(devolucao_id)
            st.session_state.pop("dash_del_id", None)
            if ok:
                limpar_cache_leitura()
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    with c2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.pop("dash_del_id", None)
            st.rerun()


def _render_cabecalho_tabela() -> None:
    h = st.columns(_COLS_HEADER)
    labels = [
        "Data + Usuário",
        "Motivo",
        "NF",
        "Valor",
        "Cod Cliente",
        "Vendedor",
        "Ações",
    ]
    for col, label in zip(h, labels):
        with col:
            if label == "Data + Usuário":
                st.markdown(
                    '<span class="lv-table-header-marker" aria-hidden="true"></span>',
                    unsafe_allow_html=True,
                )
            if label:
                cls = "lista-dash-th lista-dash-th-acoes" if label == "Ações" else "lista-dash-th"
                st.markdown(f'<p class="{cls}">{label}</p>', unsafe_allow_html=True)


def _render_acoes(
    row_id: int,
    *,
    pode_alterar: bool,
    on_edit: Callable[[int], None],
    on_delete: Callable[[int], None],
) -> None:
    st.markdown(
        '<span class="lista-dash-col-acoes-marker"></span>',
        unsafe_allow_html=True,
    )
    if not pode_alterar:
        st.markdown('<p class="lista-dash-acoes-empty">—</p>', unsafe_allow_html=True)
        return

    col_edit, col_del = st.columns(2)
    with col_edit:
        if st.button(
            "",
            key=f"dash_edit_{row_id}",
            icon=_ICON_EDITAR,
            help="Editar devolução",
            type="secondary",
        ):
            on_edit(row_id)
    with col_del:
        if st.button(
            "",
            key=f"dash_del_{row_id}",
            icon=_ICON_EXCLUIR,
            help="Excluir devolução",
            type="secondary",
        ):
            on_delete(row_id)


def _render_linha(
    row,
    *,
    pode_alterar: bool,
    on_edit: Callable[[int], None],
    on_delete: Callable[[int], None],
) -> None:
    dados = _linha_para_exibicao(row)
    cols = st.columns(_COLS_ROW)

    with cols[0]:
        st.markdown('<span class="lv-row-marker" aria-hidden="true"></span>', unsafe_allow_html=True)
        st.markdown(
            _html_celula_usuario(dados["data_txt"], dados["usuario"]),
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            _html_celula(dados["motivo"], extra_class="lv-cell-motivo"),
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            _html_badge(dados["nf"], extra_class="lv-badge-nf", title=dados["nf"]),
            unsafe_allow_html=True,
        )
    with cols[3]:
        st.markdown(
            _html_badge(dados["valor"], extra_class="lv-badge-valor", title=dados["valor"]),
            unsafe_allow_html=True,
        )
    with cols[4]:
        st.markdown(_html_celula(dados["cod_cliente"]), unsafe_allow_html=True)
    with cols[5]:
        st.markdown(
            _html_celula(
                dados["vendedor"],
                extra_class="lv-cell-vendedor lv-cell-truncate",
                title=dados["vendedor"],
            ),
            unsafe_allow_html=True,
        )
    with cols[6]:
        _render_acoes(
            row.id,
            pode_alterar=pode_alterar,
            on_edit=on_edit,
            on_delete=on_delete,
        )


def render_listagem_operacional(rows: list) -> None:
    """Tabela premium com ícones de ação lado a lado."""
    if not rows:
        st.info("Nenhuma devolução encontrada para o período selecionado.")
        return

    inject_listview_premium_css()
    pode_alterar = pode_editar()

    if st.session_state.get("dash_edit_id"):
        _dialog_editar(int(st.session_state["dash_edit_id"]))

    if st.session_state.get("dash_del_id"):
        _dialog_excluir(int(st.session_state["dash_del_id"]))

    def _abrir_editar(dev_id: int) -> None:
        st.session_state["dash_edit_id"] = dev_id
        st.session_state.pop("dash_del_id", None)

    def _abrir_excluir(dev_id: int) -> None:
        st.session_state["dash_del_id"] = dev_id
        st.session_state.pop("dash_edit_id", None)

    st.markdown('<div class="lista-premium-stable" aria-label="Listagem operacional">', unsafe_allow_html=True)
    st.markdown(
        '<span class="lista-premium-scroller-marker" aria-hidden="true"></span>',
        unsafe_allow_html=True,
    )

    total = len(rows)
    page_size = LISTVIEW_PAGE_SIZE
    total_pages = max(1, (total + page_size - 1) // page_size)
    page_key = "dash_lista_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    pagina = int(st.session_state[page_key])
    if pagina > total_pages:
        pagina = total_pages
        st.session_state[page_key] = pagina
    if pagina < 1:
        pagina = 1
        st.session_state[page_key] = pagina

    inicio = (pagina - 1) * page_size
    fim = min(inicio + page_size, total)
    slice_rows = rows[inicio:fim]

    filtro_sig = st.session_state.get("dash_lista_filtro_sig")
    if filtro_sig is not None and st.session_state.get("_lv_last_filtro") != filtro_sig:
        st.session_state[page_key] = 1
    st.session_state["_lv_last_filtro"] = filtro_sig

    with st.container(height=LISTVIEW_SCROLL_PX, border=False):
        st.markdown('<div class="lista-premium-header lista-premium-header-sticky">', unsafe_allow_html=True)
        _render_cabecalho_tabela()
        st.markdown("</div>", unsafe_allow_html=True)

        for row in slice_rows:
            _render_linha(
                row,
                pode_alterar=pode_alterar,
                on_edit=_abrir_editar,
                on_delete=_abrir_excluir,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    if total_pages > 1:
        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button(
                "Anterior",
                disabled=pagina <= 1,
                key="dash_lista_prev",
                use_container_width=True,
            ):
                st.session_state[page_key] = pagina - 1
                st.rerun()
        with nav2:
            st.caption(
                f"Página {pagina} de {total_pages} · "
                f"exibindo {inicio + 1}–{fim} de {total} registros"
            )
        with nav3:
            if st.button(
                "Próxima",
                disabled=pagina >= total_pages,
                key="dash_lista_next",
                use_container_width=True,
            ):
                st.session_state[page_key] = pagina + 1
                st.rerun()

    if not pode_alterar:
        st.caption("Perfil somente leitura — edição e exclusão disponíveis para administrador.")
