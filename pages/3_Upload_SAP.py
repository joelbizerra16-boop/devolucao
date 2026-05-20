"""Upload Dados SAP — importação para o banco."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.auth import get_current_user
from core.layout import init_authenticated_page, safe_page_run
from core.navigation import PAGE_UPLOAD
from core.navigation import PAGE_UPLOAD
from core.permissions import aviso_somente_leitura, pode_editar
from core.paths import UPLOADS_SAP_DIR
from core.styles import page_header
from services.sap_service import contar_base, importar_planilha, obter_arquivo_ativo


def _render() -> None:
    init_authenticated_page("Upload Dados SAP", "📤", page_slug=PAGE_UPLOAD)

    page_header("Upload Dados SAP", "Importe planilhas SAP (CSV ou XLSX)")
    aviso_somente_leitura()
    pode_importar = pode_editar()

    arquivo_ativo = obter_arquivo_ativo()
    info_arquivo = f" · Arquivo ativo: `{arquivo_ativo}`" if arquivo_ativo else ""
    st.caption(f"Registros SAP no banco: **{contar_base()}**{info_arquivo}")

    if st.session_state.get("sap_import_msg"):
        if st.session_state.get("sap_import_ok"):
            st.success(st.session_state["sap_import_msg"])
        else:
            st.error(st.session_state["sap_import_msg"])

    arquivo = st.file_uploader(
        "Selecione o arquivo",
        type=["csv", "xlsx", "xls"],
        help="Planilha SAP: NF, Código do cliente/fornecedor, Cliente, Cidade, Bairro, Vendedor, ValorNF, DataNF.",
        key="sap_file_uploader",
        disabled=not pode_importar,
    )

    if arquivo is not None:
        st.markdown(f"**Arquivo:** `{arquivo.name}`")

        if st.button(
            "Importar Base SAP",
            type="primary",
            use_container_width=True,
            key="btn_importar_sap",
            disabled=not pode_importar,
        ):
            if not pode_importar:
                st.warning("Usuário sem permissão.")
                st.stop()
            user = get_current_user()
            usuario = user.username if user else "sistema"
            conteudo = arquivo.getvalue()
            ok, msg, qtd, df_preview = importar_planilha(conteudo, arquivo.name, usuario=usuario)

            st.session_state["sap_import_ok"] = ok
            st.session_state["sap_import_msg"] = (
                f"{msg} ({qtd} registro(s))." if ok else msg
            )

            if ok and df_preview is not None:
                st.session_state["sap_preview_df"] = df_preview
                st.session_state["sap_preview_nome"] = arquivo.name
            elif not ok:
                st.session_state.pop("sap_preview_df", None)
                st.session_state.pop("sap_preview_nome", None)

    if "sap_preview_df" in st.session_state:
        st.markdown("---")
        st.subheader(f"Preview — {st.session_state.get('sap_preview_nome', '')}")
        preview = st.session_state["sap_preview_df"].copy()
        preview = preview.rename(
            columns={
                "nf_nfd": "NF",
                "cod_cliente": "Código do cliente/fornecedor",
                "cliente": "Cliente",
                "cidade": "Cidade",
                "bairro": "Bairro",
                "vendedor": "Vendedor",
                "valor_nf": "ValorNF",
                "data_emissao_nf": "DataNF",
            }
        )
        st.dataframe(preview, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption(
        f"Pasta oficial: `{UPLOADS_SAP_DIR}` — mantém apenas a última base importada."
    )


safe_page_run(_render, "Upload Dados SAP")
