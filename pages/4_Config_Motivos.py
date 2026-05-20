"""Configuração Motivos — cadastro de motivos de devolução (CSV)."""



from __future__ import annotations



import sys

from pathlib import Path



import streamlit as st



ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



from core.layout import init_authenticated_page, safe_page_run
from core.navigation import PAGE_MOTIVOS
from core.permissions import aviso_somente_leitura, pode_editar
from core.styles import page_header

from services.csv_repository import (

    adicionar_motivo,

    excluir_motivo,

    importar_motivos_planilha,

    ler_planilha_motivos_upload,

    listar_motivos,

    listar_motivos_df,

)





def _render() -> None:

    init_authenticated_page("Configuração Motivos", "⚙️", page_slug=PAGE_MOTIVOS)



    page_header("Configuração Motivos", "Gerencie os motivos disponíveis no cadastro de devoluções")
    aviso_somente_leitura()
    pode_alterar = pode_editar()

    motivos = listar_motivos()



    c_add, c_del = st.columns(2)



    with c_add:

        st.subheader("Adicionar")

        with st.form("form_add_motivo", clear_on_submit=True):

            descricao = st.text_input("Descrição motivo", placeholder="Ex: Produto em desacordo")

            adicionar = st.form_submit_button(
                "Adicionar",
                type="primary",
                use_container_width=True,
                disabled=not pode_alterar,
            )

        if adicionar:
            if not pode_alterar:
                st.warning("Usuário sem permissão.")
                st.stop()

            ok, msg = adicionar_motivo(descricao)

            if ok:

                st.success(msg)

                st.rerun()

            else:

                st.error(msg)



    with c_del:

        st.subheader("Excluir")

        if not motivos:

            st.info("Nenhum motivo para excluir.")

        else:

            with st.form("form_del_motivo"):

                motivo_excluir = st.selectbox("Selecione o motivo", options=motivos, key="motivo_excluir_sel")

                excluir = st.form_submit_button(
                    "Excluir",
                    use_container_width=True,
                    disabled=not pode_alterar,
                )

            if excluir:
                if not pode_alterar:
                    st.warning("Usuário sem permissão.")
                    st.stop()

                ok, msg = excluir_motivo(motivo_excluir)

                if ok:

                    st.success(msg)

                    st.rerun()

                else:

                    st.error(msg)



    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Importar motivos",
        type=["csv", "xlsx"],
        disabled=not pode_alterar,
    )

    if st.button(
        "Importar",
        type="primary",
        disabled=(uploaded_file is None) or (not pode_alterar),
    ):
        if not pode_alterar:
            st.warning("Usuário sem permissão.")
            st.stop()
        if uploaded_file is not None:

            try:

                planilha = ler_planilha_motivos_upload(uploaded_file)

                ok, msg = importar_motivos_planilha(planilha)

                if ok:

                    st.success(msg)

                    st.rerun()

                else:

                    st.error(msg)

            except Exception as exc:

                st.error(f"Erro ao ler planilha: {exc}")



    st.markdown("---")

    st.subheader("Motivos cadastrados")

    df = listar_motivos_df()

    if df.empty:

        st.info("Nenhum motivo cadastrado.")

    else:

        st.dataframe(

            df.rename(columns={"id": "ID", "descricao": "Descrição"}),

            use_container_width=True,

            hide_index=True,

        )





safe_page_run(_render, "Configuração Motivos")


