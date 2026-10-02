# Deploy do DEVOLUÇÃO em VPS Ubuntu

Este documento prepara a implantação. Ele não autoriza executar o deploy agora.

O DEVOLUÇÃO é um sistema próprio: Streamlit, Python 3.11, SQLAlchemy e PostgreSQL. Nesta etapa nenhum acesso à VPS, nenhum dump e nenhuma alteração no Supabase foram feitos.

## Arquitetura prevista

```
Internet
  -> reverse proxy já existente na VPS (não configurado nesta etapa)
    -> 127.0.0.1:DEVOLUCAO_HOST_PORT
      -> container devolucao-app (Streamlit 8501, somente na rede Docker)
        -> rede devolucao-network
          -> container devolucao-postgres:5432 (sem porta publicada no host)
```

Recursos exclusivos deste projeto:

| Recurso | Nome |
| --- | --- |
| Compose project | `devolucao` |
| Aplicação | `devolucao-app` |
| Banco | `devolucao-postgres` |
| Rede | `devolucao-network` |
| Volume do PostgreSQL | `devolucao-postgres-data` |
| Volume de dados da app | `devolucao-data` (`/app/data`) |
| Volume de uploads, inclusive SAP | `devolucao-uploads` (`/app/uploads`) |
| Volume de logs | `devolucao-logs` (`/app/logs`) |

PostgreSQL 17. A porta 5432 não é publicada no host. O Streamlit escuta em `0.0.0.0:8501` apenas dentro do container e é publicado somente em `127.0.0.1`.

Não usar `network_mode: host`. Não reutilizar rede, volume, banco, usuário PostgreSQL ou container de outro sistema.

## Ambientes

A variável `DEVOLUCAO_ENV` é a única chave de ambiente. As funções estão em `core/environment.py`: `is_production()`, `is_development()`, `is_test()`.

| Valor | Banco sem `DATABASE_URL` | Segredo de autenticação | Admin `admin` / `admin123` |
| --- | --- | --- | --- |
| `development` (padrão se a variável não existir) | SQLite em `data/devolucao.db` | Pode usar o valor padrão de desenvolvimento | Criado somente se o usuário `admin` ainda não existir |
| `test` | Igual a development | Igual a development | Igual a development |
| `production` | Falha imediata. SQLite é proibido | `DEVOLUCAO_AUTH_SECRET` obrigatória, não pode ser vazia nem o valor padrão | Não é criado |

`DB_SSLMODE` define o SSL do PostgreSQL. Se a variável não existir, o padrão do código continua `require`, para não enfraquecer Supabase. No compose deste projeto o padrão é `disable`, porque o PostgreSQL privado não tem TLS. Se a `DATABASE_URL` de produção apontar para Supabase, use `DB_SSLMODE=require`.

Pool, sem alteração de tuning: `DB_CONNECT_TIMEOUT` (10), `DB_POOL_RECYCLE` (300), `DB_POOL_SIZE` (5), `DB_POOL_MAX_OVERFLOW` (10).

O modelo é `docker-compose.prod.yml` mais um `.env` real, fora do Git. Os nomes estão em `.env.example`. Nenhuma senha entra na imagem nem no YAML.

Senha com `@`, `:`, `/`, `#`, `%` ou `$` deve ser percent-encoded dentro de `DATABASE_URL`. O compose não monta a URL a partir de pedaços.

Dentro da rede Docker o host do banco é `devolucao-postgres`. Não usar `localhost` para o banco.

## Persistência

Diretórios confirmados no código:

- `data/` — SQLite local de development e arquivos de runtime. Em produção o banco é o PostgreSQL do volume `devolucao-postgres-data`.
- `uploads/sap/` — base SAP ativa. A regra de manter o arquivo ativo nessa pasta não foi alterada.
- `uploads/sap/.backup` — cópia usada por `services/sap_service.py` durante a troca da base. O backup continua dentro de `uploads/` e portanto no volume `devolucao-uploads`.
- `logs/system.log` e `logs/import_sap.log`.

Recriar o container da aplicação não apaga esses volumes. Não montar `/`, `/etc`, `/var`, `/home` ou `/opt` inteiros.

## Build, start, stop, restart, logs e health

No diretório do projeto, com o `.env` real ao lado do compose:

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs devolucao-app
docker compose -f docker-compose.prod.yml logs devolucao-postgres
docker compose -f docker-compose.prod.yml restart devolucao-app
docker compose -f docker-compose.prod.yml stop
docker compose -f docker-compose.prod.yml start
```

Healthchecks:

- PostgreSQL: `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB`, com usuário e banco interpolados pelo Compose a partir do `.env`. A senha não entra no healthcheck.
- Streamlit: `http://127.0.0.1:8501/_stcore/health`.

A aplicação só depende do Postgres depois que o healthcheck do banco passa. Política de reinício: `restart: unless-stopped`.

Parar esta stack:

```bash
docker compose -f docker-compose.prod.yml stop
```

Remover os containers desta stack, preservando volumes:

```bash
docker compose -f docker-compose.prod.yml down
```

`down -v` apaga os volumes declarados neste compose, inclusive o banco e os uploads. Só usar depois de confirmar que os nomes são exclusivamente `devolucao-postgres-data`, `devolucao-data`, `devolucao-uploads` e `devolucao-logs`, e que existe backup válido.

Proibido nesta VPS, para qualquer projeto: `docker system prune`, `docker volume prune`, `docker network prune`, `docker container prune`, `docker image prune -a`, e qualquer `docker stop`/`docker rm` genérico sobre todos os containers.

## Atualização e rollback

Atualização:

1. Backup do PostgreSQL exclusivo, conforme a seção de backup.
2. Guardar a tag ou o commit atualmente em execução.
3. Atualizar somente o diretório deste projeto.
4. `docker compose -f docker-compose.prod.yml build`.
5. `docker compose -f docker-compose.prod.yml up -d`.
6. Conferir health e o validador de leitura.

Rollback da aplicação: voltar ao commit anterior, rebuild e `up -d`. Os volumes permanecem. Rollback de dados é restaurar o dump no banco exclusivo, nunca em outro banco.

Não há imagem publicada em registry nesta etapa. A imagem local prevista é `devolucao-app:local`.

## Backup e restore

Script futuro: `scripts/backup_postgres.sh`.

```bash
DATABASE_URL='postgresql://USUARIO:SENHA@devolucao-postgres:5432/devolucao' \
  ./scripts/backup_postgres.sh /caminho/exclusivo/devolucao/backups
```

O script exige `pg_dump`, grava `devolucao_YYYYMMDDTHHMMSSZ.dump` em formato custom, falha se o dump falhar e não apaga dumps anteriores. Um arquivo `.partial` interrompido é removido; dumps concluídos não são. A URL não é impressa. `--no-owner` e `--no-privileges` existem para o restore caber no usuário exclusivo `devolucao_user`, sem depender dos papéis do Supabase.

Restore, somente no banco já comprovado como exclusivo do DEVOLUÇÃO e de preferência vazio:

```bash
pg_restore --no-owner --no-privileges --dbname="$DATABASE_URL" /caminho/devolucao_TIMESTAMP.dump
```

Não usar `pg_restore --clean` sem uma auditoria que prove que o alvo é o banco vazio deste projeto. `--clean` emite `DROP` dos objetos do dump.

## Migrations e sequences

`run_migrations()` cria tabelas ausentes com `create_all`, adiciona colunas com `ADD COLUMN IF NOT EXISTS` no PostgreSQL e cria índices com `IF NOT EXISTS`. Não foi introduzido `DROP TABLE`, `DROP SCHEMA`, `TRUNCATE` nem recriação destrutiva.

Comportamento já existente, mantido e restrito:

- Em SQLite antigo, `_migrar_sqlite_legado()` pode renomear `devolucoes` para `devolucoes_legado` quando falta `data_lancamento`. Esse caminho não roda quando o dialeto é PostgreSQL.
- `_migrar_coluna_tratativa()` preenche `tratativa` vazia com `Aguardando`. Não apaga linhas.

Seeds:

- Motivos padrão só entram se a tabela `motivos` estiver vazia.
- `admin` / `admin123` só é criado fora de `production`, e só quando o usuário `admin` não existe. Produção não cria, não altera senha e não sobrescreve usuário migrado.

IDs autoincrementais confirmados nos models: `usuarios.id`, `motivos.id`, `dados_sap.id`, `devolucoes.id`. No PostgreSQL isso vira sequences, em geral `usuarios_id_seq`, `motivos_id_seq`, `dados_sap_id_seq` e `devolucoes_id_seq`. A lista real deve ser lida depois do restore. Esta rodada não ajustou sequence nenhuma.

Depois do restore, para cada tabela, conferir `MAX(id)` com o próximo valor da sequence (`last_value` e `is_called` em `pg_sequences`). Se o próximo valor for menor ou igual ao maior ID, a sequence precisa ser alinhada antes de novos inserts. O script `scripts/validate_database.py` apenas lê essas informações.

## Migração futura Supabase para PostgreSQL

Ordem obrigatória:

1. Auditoria somente leitura do Supabase.
2. `pg_dump` completo da origem.
3. Auditoria somente leitura da VPS.
4. Escolha de porta, diretório e nomes exclusivos.
5. Criação do PostgreSQL exclusivo.
6. `pg_restore` nesse banco.
7. Validação origem contra destino.
8. Deploy da aplicação apontando para o banco da VPS.
9. Testes.
10. Produção.

Não usar automaticamente `migrate_sqlite_to_supabase.py` nem `scripts/migrate_sqlite_to_supabase.py` como migração do Supabase para a VPS. Esses scripts partem do SQLite e não foram validados como cópia completa do schema atual.

O catálogo real manda. Models atuais declaram `usuarios`, `motivos`, `dados_sap` e `devolucoes`, mas a validação tem de listar todas as tabelas encontradas, não só essas.

Comparar com `scripts/validate_database.py` na origem e no destino: `SELECT 1`, versão, tabelas, quantidade de registros, maior `id`, mínimo e máximo das colunas de data e `last_value` das sequences. O script é somente leitura.

## Segurança

- `DEVOLUCAO_AUTH_SECRET` é obrigatória em production. Valor vazio ou o segredo padrão de development fazem a aplicação falhar.
- O segredo padrão permanece disponível apenas fora de production, para o login local continuar funcionando.
- Logs passam por mascaramento de URL PostgreSQL, segredo de autenticação, `POSTGRES_PASSWORD`, hash bcrypt, `?auth=` e cookie `devolucao_auth`.
- `test_real.py` deixou de imprimir a URL completa.
- Traceback na tela existe em development e test. Em production a interface mostra mensagem genérica; o traceback continua em `logs/system.log`.
- O container da aplicação define `STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=none`.
- A aplicação roda como usuário `devolucao` (uid 10001), sem `privileged` e sem acesso ao socket do Docker.

Pendência de autenticação, sem mudança nesta rodada: a sessão persistente continua assinada com HMAC e transportada em `?auth=` e em cookie gravado por JavaScript, sem `HttpOnly`. Reescrever isso agora arriscaria o login. Antes da exposição pública, o proxy não deve registrar query string completa, e uma evolução futura deve tirar o token da URL.

## Auditoria futura da VPS — somente leitura

O primeiro acesso à VPS não cria, não altera e não para nada. Executar e guardar a saída:

```bash
pwd
whoami
hostname
df -h
free -h
docker ps
docker ps -a
docker compose ls
docker network ls
docker volume ls
ss -tulpn
```

Inspecionar os diretórios onde os outros sistemas já estão. Não assumir que uma porta, um nome de volume, uma rede, um banco ou um diretório estão livres.

Caminho conceitual preferido: `/opt/devolucao`. Não criar agora. Se `/opt/devolucao` já existir, não sobrescrever. Primeiro identificar o dono. Dúvida significa parar.

Reverse proxy: não configurar agora. No futuro, identificar se a VPS usa Caddy, Nginx, Traefik ou outro, qual domínio será do DEVOLUÇÃO e qual arquivo é exclusivo. Acrescentar somente o bloco deste sistema, apontando para `127.0.0.1` na porta escolhida depois da auditoria. Não alterar certificado nem domínio de outro sistema.

Qualquer dúvida sobre porta, container, volume, rede, banco, diretório, domínio, proxy ou serviço: parar e reportar.
