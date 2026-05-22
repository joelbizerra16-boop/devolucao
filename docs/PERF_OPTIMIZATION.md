# Otimização de performance (NASA mode)

## Profiling (baseline)

| Área | Gargalo identificado |
|------|----------------------|
| Dashboard | PDF/Excel gerados a cada rerun; listview com até 500×8 widgets |
| SQLAlchemy | `commit()` após cada SELECT; 3 sessões por cache miss de gráficos |
| PostgreSQL | `extract(year/month)` no WHERE (índice menos eficiente) |
| Streamlit | CSS reinjetado a cada rerun; bootstrap DB em todo `app.py` rerun |
| SAP import | `listar_todos_como_dicts().all()` (backup completo) |

## Alterações aplicadas

- **DB:** sessões read-only sem commit; `get_write_session()` para writes; pool `size`/`max_overflow` configurável
- **Dashboard repo:** filtro por intervalo de datas; `obter_agregacoes_graficos()` em uma sessão
- **Cache:** PDF/Excel export; gráficos; TTL 300s mantido
- **Listview:** paginação 50 linhas/página (`LISTVIEW_PAGE_SIZE`)
- **CSS:** injeção uma vez por sessão Streamlit
- **Bootstrap:** `_db_ready` em `session_state`
- **Monitor:** `core/perf_monitor.py` → `logs/system.log` (tag `perf`, limiar 400ms)

## Variáveis de ambiente

| Variável | Padrão | Uso |
|----------|--------|-----|
| `PERF_MONITOR` | `1` | Logs de operações lentas |
| `PERF_SLOW_MS` | `400` | Limiar em ms |
| `DB_POOL_SIZE` | `5` | Pool SQLAlchemy |
| `DB_POOL_MAX_OVERFLOW` | `10` | Overflow do pool |

## Medição

Com `PERF_MONITOR=1`, abra `logs/system.log` e filtre `perf:` após usar o Dashboard e exportações.
