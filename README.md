# Relatório Operacional de Devoluções

Sistema em **Python + Streamlit** para consulta, cadastro em CSV, upload SAP e configuração de motivos.

## Menu

| Tela | Função |
|------|--------|
| Consultar Devoluções | Visão operacional (métricas, filtros, tabela) |
| Cadastro Devolução (`2_Cadastrar_Devolucao.py`) | Formulário salvo em `data/devolucoes.csv` |
| Upload Dados SAP | Importa CSV/XLSX para `uploads/sap/` |
| Configuração Motivos | CRUD de motivos em `data/motivos.csv` |

## Executar

```bash
cd projeto_devolucao
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Login: **admin** / **admin123**

## Arquivos de dados

```
data/devolucao.db      # SQLite — devoluções e usuários
data/motivos.csv       # motivos (cadastro/upload)
uploads/sap/
```

PostgreSQL/Supabase: defina `DATABASE_URL` no ambiente.
