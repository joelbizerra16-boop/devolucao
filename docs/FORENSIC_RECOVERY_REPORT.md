# Relatório de Recuperação Forense — Dados Reais

**Data:** 2026-05-22  
**Origem principal:** `FINALIZADO/projeto_devolucaoV01/data/devolucao.db` (7 devoluções) + agregação de 5 cópias SQLite locais.

## Resumo executivo

| Métrica | Esperado (ontem) | Encontrado localmente | Após recuperação no Supabase |
|--------|-------------------|------------------------|------------------------------|
| Usuários | ~8 | **3** por arquivo SQLite | **4** (+1 `visitante`) |
| Devoluções reais | ~35 | **7** (tabela `devolucoes`) | **7** |
| Motivos | reais | 5 SQLite + 31 CSV | **36** |
| Dados SAP | — | 9838 | **9838** |

**Conclusão:** Os ~8 usuários e ~35 devoluções **não existem** em nenhum `devolucao.db` local analisado. O máximo recuperável offline era **7 devoluções reais** (V01) e **3 usuários** (+ CSV de motivos). A tabela `devolucoes_legado` (12 linhas) contém **dados demo** (`DEV-2026-0001`…) e **não foi migrada**.

## Fontes analisadas

1. `projeto_devolucao/data/devolucao.db`
2. `FINALIZADO/projeto_devolucaoV01/data/devolucao.db` ← mais devoluções (7)
3. `FINALIZADO/projeto_devolucaoV02/data/devolucao.db`
4. `FINALIZADO/projeto_devolucaoV03/data/devolucao.db`
5. `FINALIZADO/projeto_devolucao/data/devolucao.db`

## Tabelas SQLite

| Tabela | Registros | Migrar? |
|--------|-----------|---------|
| usuarios | 3 | Sim (login ausente) |
| motivos | 5 | Sim |
| devolucoes | 5–7 | Sim (reais) |
| devolucoes_legado | 12 | **Não** (demo) |
| historico_devolucoes | 12 | Não (auditoria antiga) |
| auditoria_logs | 0 | — |
| dados_sap | 9838 | Já no Supabase |

## Recuperado nesta execução

- **1 usuário:** `visitante` (novo id 4 — sem sobrescrever `camilly001` id 3)
- **1 devolução:** id **3** — NF `1386950` (estava só no V01)
- **Motivos:** complemento via `data/motivos.csv` (descrições únicas)

## Conflitos (não sobrescritos)

| id | Supabase (atual) | SQLite V01 (real) |
|----|------------------|-------------------|
| 1 | NF 1406244 / 2026-05-20 | NF 123 / 2026-05-18 |
| 2 | NF 1406239 / 2026-05-19 | NF 1406428 / 2026-05-19 |

Para alinhar ids 1 e 2 ao histórico real, é necessária **correção manual** no Supabase (ou exportar PG, editar, reimportar) — o script respeitou a regra de não sobrescrever.

## Como reexecutar

```powershell
python scripts/forensic_recovery_report.py    # somente leitura
python scripts/audit_all_sqlite_sources.py    # audita todas as cópias .db
python scripts/forensic_recover_production.py # migra faltantes
```

Relatório JSON detalhado (local): `logs/forensic_recovery_report.json`
