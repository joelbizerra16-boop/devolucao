# Resumo Operacional de Devoluções

**Data da entrega:** 2026-06-18  
**Módulo:** Resumo Operacional de Devoluções  
**Tipo:** Nova página analítica independente do Dashboard

---

## Objetivo da funcionalidade

A página **Resumo** oferece uma visão operacional consolidada das devoluções em um período selecionado. Diferente do Dashboard executivo (focado em status, SLA e listview detalhada), o Resumo concentra-se em **indicadores agregados**, **gráficos Top 5** e uma **tabela analítica dinâmica** com exportação Excel.

O usuário pode filtrar por mês, ano, cliente, motivo e tratativa; visualizar KPIs financeiros e de volume; analisar rankings de motivos e clientes; e explorar dados agrupados por motivo ou cliente, com ordenação e percentuais coerentes com o critério escolhido.

---

## Arquitetura utilizada

A implementação segue integralmente o padrão já adotado pelo projeto:

```
pages/7_Resumo.py
    └── services/resumo_operacional_service.py
            └── repositories/resumo_operacional_repository.py
                    └── PostgreSQL (Supabase) via SQLAlchemy / modelo Devolucao
```

### Pages

| Arquivo | Responsabilidade |
|---------|------------------|
| `pages/7_Resumo.py` | Orquestração da UI: filtros, KPIs, gráficos, tabela analítica e exportação |

A página utiliza `init_authenticated_page`, `safe_page_run` e `track_page("resumo")`, no mesmo padrão das demais telas autenticadas.

### Services

| Arquivo | Responsabilidade |
|---------|------------------|
| `services/resumo_operacional_service.py` | Formatação de KPIs, montagem de gráficos Plotly, preparação de DataFrames, exportação Excel e funções com `@st.cache_data` |

O service reutiliza utilitários do Dashboard (`MESES_LABEL`, `CHART_GRID`, `CHART_HEIGHT`, cores, rótulos e período padrão) sem alterar a lógica do Dashboard.

### Repository

| Arquivo | Responsabilidade |
|---------|------------------|
| `repositories/resumo_operacional_repository.py` | Consultas SQL agregadas via SQLAlchemy; dataclass `FiltrosResumo`; filtros de período, cliente, motivo e tratativa |

Reutiliza `_filtro_mes_ano` de `repositories/dashboard_repository.py` para consistência de filtro temporal.

### Components

| Componente | Uso no Resumo |
|------------|---------------|
| `components/cards.py` | `render_resumo_cards()` — quatro KPIs em layout 1:1:1:1 |
| `components/chart_card.py` | `render_plotly_in_card()` — quatro gráficos horizontais Top 5 |
| `components/tabelas.py` | `render_tabela_resumo_analitica()` — tabela dinâmica com heat map na coluna Percentual |
| `components/sidebar.py` | Link de navegação "Resumo" abaixo do Dashboard |

### Navegação

| Arquivo | Alteração |
|---------|-----------|
| `core/navigation.py` | Constante `PAGE_RESUMO = "resumo"` e entrada em `PAGES` apontando para `pages/7_Resumo.py` |
| `components/sidebar.py` | `st.page_link` para Resumo com ícone 📈 e `query_params` persistentes |

A navegação preserva o mecanismo existente de `session_state` + `?page=` na URL.

### Cache

| Arquivo | Alteração |
|---------|-----------|
| `core/cache_read.py` | Registro das quatro funções cacheadas do Resumo em `limpar_cache_leitura()` |
| `services/resumo_operacional_service.py` | `@st.cache_data(ttl=TTL_DASHBOARD)` (300 segundos) em: `carregar_resumo_cache`, `obter_graficos_resumo_cache`, `carregar_tabela_resumo_cache`, `obter_opcoes_filtros_cache` |

O botão **Atualizar** na página chama `limpar_cache_leitura()` e `st.rerun()`, invalidando todos os caches de leitura do sistema.

### Consultas SQL

Todas as agregações são executadas no PostgreSQL via SQLAlchemy, utilizando:

- `COUNT`, `SUM`, `COALESCE`, `MAX`, `GROUP BY`, `ORDER BY`, `LIMIT`
- Filtros parametrizados por `FiltrosResumo` (mês/ano, cliente, motivo, tratativa)
- Classificação de tratativa alinhada a `core.tratativa_utils.classificar_tratativa`

Nenhum agrupamento analítico é feito em Python — o service apenas formata e apresenta os resultados.

---

## Funcionalidades implementadas

### Nova página — Resumo

Arquivo: `pages/7_Resumo.py`

- Título: **Resumo**
- Subtítulo: *Indicadores operacionais e análise agregada de devoluções*
- Ícone: 📈
- Slug de navegação: `resumo`
- Seções: filtros → KPIs → 4 gráficos (2×2) → tabela analítica → exportação Excel

### Menu lateral — Inclusão da opção Resumo

Em `components/sidebar.py`, o link **Resumo** foi adicionado imediatamente abaixo de **Dashboard**, com:

- Caminho: `pages/7_Resumo.py`
- Ícone: 📈
- Query params: `page=resumo`

### Filtros

Todos integrados ao PostgreSQL via `repositories/resumo_operacional_repository.py`:

| Filtro | Comportamento |
|--------|---------------|
| **Mês** | Selectbox com `MESES_LABEL`; convertido para número via `mes_label_para_numero` |
| **Ano** | Selectbox com anos disponíveis (`obter_anos_disponiveis`) |
| **Cliente** | Opções dinâmicas do período (`listar_opcoes_cliente`); chave por `cod_cliente` |
| **Motivo** | Opções dinâmicas do período (`listar_opcoes_motivo`); valores distintos de `motivo_devolucao` |
| **Tratativa** | Opções de `TRATATIVA_FILTROS_UI`; filtro SQL alinhado às categorias Aguardando, Em Análise, Concluído e Recusado |

Botão **Atualizar** invalida o cache e recarrega os dados.

---

### KPIs implementados

Quatro cards em layout **1:1:1:1** (`render_resumo_cards`):

| KPI | Rótulo na tela | Fórmula | Origem SQL |
|-----|----------------|---------|------------|
| Total de Devoluções | Total de Devoluções | `COUNT(Devolucao.id)` | `obter_kpis()` |
| Valor Total Devolvido | Valor Total Devolvido | `SUM(Devolucao.valor_nf)` | `obter_kpis()` |
| Ticket Médio | Ticket Médio | `valor_total ÷ quantidade_devolucoes` | Calculado em `_calcular_ticket_medio()` após consulta |
| Valor Médio por Dia | Média Móvel *(rótulo do card)* | `valor_total ÷ dias_do_mês` | Calculado em `_calcular_media_diaria_valor()` usando `calendar.monthrange` |

**Detalhes das fórmulas:**

1. **Total de Devoluções** — contagem de registros que atendem aos filtros aplicados.
2. **Valor Total Devolvido** — soma de `valor_nf` com `COALESCE` para zero quando nulo.
3. **Ticket Médio** — `soma_valor_nf / total_devolucoes`; retorna `0` se `total <= 0`.
4. **Valor Médio por Dia** — `soma_valor_nf / dias_do_mês` (todos os dias do mês calendário, independente de haver devoluções naquele dia). Exibido como `R$ X,XX / dia`.

Os cards **Maior Motivo** e **Cliente com Maior Incidência** foram deliberadamente **não incluídos** no Resumo; esses indicadores permanecem exclusivos do Dashboard.

---

### Gráficos

Quatro gráficos de barras horizontais (Plotly), dispostos em grade 2×2:

| Gráfico | Função repository | Agregação SQL |
|---------|-------------------|---------------|
| Top 5 Motivos por Quantidade | `top5_motivos_quantidade` | `GROUP BY motivo_devolucao` → `ORDER BY COUNT DESC` → `LIMIT 5` |
| Top 5 Motivos por Valor | `top5_motivos_valor` | `GROUP BY motivo_devolucao` → `ORDER BY SUM(valor_nf) DESC` → `LIMIT 5` |
| Top 5 Clientes por Quantidade | `top5_clientes_quantidade` | `GROUP BY cod_cliente` → `ORDER BY COUNT DESC` → `LIMIT 5` |
| Top 5 Clientes por Valor | `top5_clientes_valor` | `GROUP BY cod_cliente` → `ORDER BY SUM(valor_nf) DESC` → `LIMIT 5` |

Cores reutilizadas do Dashboard: `COR_DEVOLUCOES` (quantidade) e `COR_FINANCEIRO` (valor). Layout horizontal com rótulos fora das barras e grid `CHART_GRID`.

Todas as agregações ocorrem diretamente no PostgreSQL; o service apenas monta as figuras Plotly a partir das tuplas retornadas.

---

### Tabela Analítica

#### Primeiro grupo de RadioButtons — Analisar por

| Opção | Agrupamento SQL |
|-------|-----------------|
| **Motivos** | `GROUP BY motivo_devolucao` |
| **Clientes** | `GROUP BY cod_cliente` (com `MAX(cliente)` para rótulo) |

#### Segundo grupo de RadioButtons — Classificar por

| Opção | Ordenação SQL |
|-------|---------------|
| **Quantidade** | `ORDER BY COUNT(id) DESC` |
| **Valor** | `ORDER BY SUM(valor_nf) DESC` |

#### Colunas exibidas

**Modo Motivos:** Motivo, Quantidade, Valor Total, Percentual  
**Modo Clientes:** Código, Cliente, Quantidade, Valor Total, Percentual

A tabela é dinâmica: a troca de modo ou ordenação dispara nova consulta via `carregar_tabela_resumo_cache()` → `listar_agregado_tabela()`.

Função central: `listar_agregado_tabela(filtros, por_cliente, por_valor)` — consulta única parametrizada com agrupamento e ordenação no PostgreSQL.

---

### Percentuais

O percentual acompanha o critério selecionado no segundo RadioButton:

| Classificar por | Fórmula do percentual |
|-----------------|----------------------|
| **Quantidade** | `(quantidade_do_item ÷ total_quantidade) × 100` |
| **Valor** | `(valor_total_do_item ÷ soma_valor_nf) × 100` |

Implementado em `_calcular_percentual_agregado()` no repository. Arredondamento com duas casas decimais.

---

### Heat Map

A coluna **Percentual** utiliza visualização tipo heat map:

1. **Preferencial:** `st.column_config.ProgressColumn` (Streamlit ≥ 1.33, ex.: 1.53.0 instalado)
2. **Alternativa:** `ProgressBarColumn` em versões mais recentes do Streamlit
3. **Fallback:** Pandas Styler com `_heatmap_percentual_styler()` — fundo `rgba(47, 128, 237, alpha)` proporcional ao percentual (0–100%)

A detecção é feita em `_config_coluna_percentual()` em `components/tabelas.py`, garantindo compatibilidade sem quebrar em versões distintas do Streamlit.

---

### Exportação Excel

Botão **Exportar Excel** na seção da tabela analítica.

| Aspecto | Comportamento |
|---------|---------------|
| Dados exportados | Exatamente o DataFrame exibido na tela |
| Filtros | Respeitados (mesmo cache/consulta da visualização) |
| Modo | Colunas conforme Motivos ou Clientes |
| Ordenação | Mesma ordem da consulta SQL (`por_valor`) |
| Percentuais | Exportados como fração decimal (0.0–1.0) com formato `0.0%` no Excel |
| Valor Total | Convertido de texto `R$` para número via `_parse_valor_total_excel` |
| Nome do arquivo | `Resumo_Operacional_YYYYMMDD_HHMMSS.xlsx` |
| Planilha | Aba "Resumo"; cabeçalho em negrito; freeze panes; auto-filter; largura de colunas ajustada |

Função: `export_tabela_resumo_excel_bytes()` em `services/resumo_operacional_service.py`.

---

### Performance

Todas as agregações analíticas utilizam operações SQL nativas:

| Operação | Uso |
|----------|-----|
| `GROUP BY` | Agrupamento por motivo ou cliente |
| `COUNT` | Quantidade de devoluções |
| `SUM` | Valor total devolvido |
| `ORDER BY` | Ordenação dinâmica (quantidade ou valor) |
| `LIMIT` | Top 5 nos gráficos |

**Evitado em Python:** agregações, ordenações e limitações de ranking. O Python limita-se a formatação, montagem de gráficos Plotly e preparação do DataFrame para exibição/exportação.

Cache com TTL de 300 segundos (`TTL_DASHBOARD`) reduz consultas repetidas em reruns do Streamlit.

---

### Compatibilidade

| Ajuste | Descrição |
|--------|-----------|
| **Constantes gráficas** | Import de `CHART_GRID`, `CHART_HEIGHT` e demais constantes de `services/dashboard_service.py` — corrige `NameError: CHART_GRID is not defined` |
| **Streamlit ProgressColumn** | Substituição de `ProgressBarColumn` (inexistente na 1.53.0) por detecção dinâmica `ProgressColumn` / `ProgressBarColumn` / Styler fallback |
| **Reuso de período** | `obter_anos_disponiveis` e `obter_periodo_padrao` importados do Dashboard para consistência |

---

### Ajustes visuais

| Ajuste | Local | Descrição |
|--------|-------|-----------|
| Layout KPIs Resumo | `components/cards.py` | Quatro cards em `st.columns(4)` — proporção 1:1:1:1 |
| RadioButtons tabela | `pages/7_Resumo.py` | Dois grupos horizontais: "Analisar por" e "Classificar por", com colunas proporcionais `[2.4, 1.15, 2.5, 1.35]` |
| Espaçamento | `pages/7_Resumo.py` | Separador `---` entre gráficos e tabela; `st.write("")` para alinhamento do botão Exportar |
| Altura tabela | `components/tabelas.py` | `_altura_tabela_resumo()` — altura dinâmica até 640px |
| Card Principal Motivo (Dashboard) | `core/theme.py`, `core/styles.py`, `components/cards.py` | Fonte ~20% menor (`TYPE_KPI_PRINCIPAL_MOTIVO = 0.65rem`); máximo 2 linhas com ellipsis (`-webkit-line-clamp: 2`) — **apenas Dashboard**, sem alterar lógica |

---

### Correções realizadas

| # | Problema | Correção |
|---|----------|----------|
| 1 | `NameError: CHART_GRID is not defined` ao renderizar gráficos | Import de `CHART_GRID` e demais constantes de `dashboard_service` |
| 2 | `AttributeError: ProgressBarColumn` no Streamlit 1.53.0 | Camada de compatibilidade `_config_coluna_percentual()` com fallback Styler |
| 3 | Percentual sempre calculado por quantidade, mesmo com classificação por Valor | `_calcular_percentual_agregado(por_valor=True)` usa `valor_total / soma_valor_nf` |
| 4 | Valor Médio por Dia calculado incorretamente (média móvel de contagem diária) | Substituído por `valor_total ÷ dias_do_mês` em `_calcular_media_diaria_valor()` |
| 5 | Ordenação por Valor não refletida na tabela | Parâmetro `por_valor` propagado até `ORDER BY SUM(valor_nf) DESC` em `listar_agregado_tabela()` |
| 6 | Exportação Excel com percentuais e valores em formato de tela | `_preparar_df_exportacao_tabela_resumo()` converte para tipos numéricos e formatos Excel |
| 7 | Heat map quebrava sem `ProgressColumn` | Fallback `_heatmap_percentual_styler()` com gradiente RGB |
| 8 | Filtro de tratativa inconsistente com classificação do sistema | Expressões SQL `_expr_aguardando`, `_expr_em_analise`, etc. alinhadas a `tratativa_utils` |

---

### Banco de Dados

| Item | Status |
|------|--------|
| Tabelas criadas | **Nenhuma** |
| Migrations | **Nenhuma** |
| Models alterados (`database/models.py`) | **Nenhum** |
| Views | **Nenhuma** |
| Triggers | **Nenhuma** |
| Procedures | **Nenhuma** |

Toda a implementação reutiliza a tabela existente `devolucoes` (modelo `Devolucao`) e consultas via SQLAlchemy sobre o PostgreSQL (Supabase).

---

### Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| `pages/7_Resumo.py` | Página Streamlit do Resumo Operacional |
| `services/resumo_operacional_service.py` | Service com KPIs, gráficos, cache e exportação Excel |
| `repositories/resumo_operacional_repository.py` | Repository com agregações SQL e filtros |
| `tests/test_resumo_operacional.py` | Testes unitários (percentual, KPIs, exportação, compatibilidade) |
| `docs/IMPLEMENTACAO_RESUMO_OPERACIONAL.md` | Este documento |

---

### Arquivos alterados

| Arquivo | Alteração |
|---------|-----------|
| `components/cards.py` | `RESUMO_CARD_CONFIG`, `render_resumo_cards()`; estilo compacto do card Principal Motivo no Dashboard |
| `components/sidebar.py` | Link de navegação "Resumo" |
| `components/tabelas.py` | Tabela analítica do Resumo; `_config_coluna_percentual()`; heat map com fallback Styler |
| `core/navigation.py` | `PAGE_RESUMO` e registro em `PAGES` |
| `core/cache_read.py` | Invalidação dos caches do Resumo em `limpar_cache_leitura()` |
| `core/theme.py` | Constante `TYPE_KPI_PRINCIPAL_MOTIVO` |
| `core/styles.py` | Classe CSS `.op-card-value--principal-motivo` com line-clamp |

**Não alterados (preservados):**

- `pages/6_Dashboard.py`
- `repositories/dashboard_repository.py`
- `database/models.py`
- `services/dashboard_service.py` (apenas consumido como dependência)

---

### Componentes reutilizados

| Componente / Módulo | Uso |
|---------------------|-----|
| `components/chart_card.py` | `render_plotly_in_card` — encapsulamento visual dos gráficos |
| `components/cards.py` | Infraestrutura `_render_card`, CSS premium (`inject_operational_cards_premium_css`) |
| `core/layout.py` | `init_authenticated_page`, `safe_page_run` |
| `core/styles.py` | `page_header`, estilos de cards |
| `core/theme.py` | Tipografia e tokens visuais |
| `core/perf_monitor.py` | `track_page("resumo")` |
| `core/tratativa_constants.py` | `TRATATIVA_FILTROS_UI`, `TRATATIVA_FILTRO_TODOS` |
| `core/tratativa_utils.py` | Referência para alinhamento das expressões SQL de tratativa |
| `core/cache_read.py` | `TTL_DASHBOARD`, `limpar_cache_leitura` |
| `core/navigation.py` | Navegação persistente com query params |
| `core/db.py` | `get_session` — sessões de leitura |
| `database/models.py` | Modelo `Devolucao` |
| `repositories/dashboard_repository.py` | `_filtro_mes_ano` |
| `services/dashboard_service.py` | Período, meses, cores, layout Plotly, constantes de gráfico |
| `services/devolucao_service.py` | `_formatar_valor_br` |
| `openpyxl` (via pandas ExcelWriter) | Geração do arquivo `.xlsx` |

---

### Resultado final

O sistema passou a possuir um módulo independente denominado **Resumo Operacional de Devoluções**, acessível pelo menu lateral.

- A implementação preserva integralmente a arquitetura existente (page → service → repository → PostgreSQL).
- Não houve alteração estrutural no banco de dados.
- Toda a lógica analítica utiliza PostgreSQL (Supabase) com agregações SQL.
- O **Dashboard original permaneceu inalterado** em lógica de negócio; apenas o card "Principal Motivo" recebeu ajuste visual de tipografia.
- Testes unitários em `tests/test_resumo_operacional.py` cobrem percentuais, KPIs, filtros, exportação Excel e compatibilidade do heat map.

---

## Fluxo de dados (referência)

```
[Filtros UI] → FiltrosResumo
      ↓
[Repository] → SQL agregado (KPIs / Top5 / Tabela)
      ↓
[Service]    → Formatação + Plotly + DataFrame + Excel
      ↓
[Components] → Cards / Gráficos / Tabela com heat map
```

---

## Validação

- [x] Todas as funcionalidades da entrega documentadas
- [x] Arquitetura, filtros, KPIs, gráficos, tabela, percentuais, heat map e exportação descritos
- [x] Performance, compatibilidade, ajustes visuais e correções listados
- [x] Arquivos criados e alterados inventariados
- [x] Ausência de alterações no banco confirmada
- [x] Nenhuma alteração de código realizada para produção deste documento

**Caminho do arquivo:** `docs/IMPLEMENTACAO_RESUMO_OPERACIONAL.md`
