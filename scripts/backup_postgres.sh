#!/usr/bin/env bash
# Backup lógico do PostgreSQL informado em DATABASE_URL.
# Não imprime a URL, não apaga backups anteriores e não escolhe outro banco.
# Uso: DATABASE_URL='postgresql://...' ./scripts/backup_postgres.sh [diretorio]
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Uso: DATABASE_URL=postgresql://... $0 [diretorio]"
  exit 0
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERRO: DATABASE_URL é obrigatória e não pode ser vazia." >&2
  exit 1
fi

case "${DATABASE_URL}" in
  postgresql://*|postgres://*) ;;
  *)
    echo "ERRO: DATABASE_URL deve ser PostgreSQL. SQLite não é aceito neste backup." >&2
    exit 1
    ;;
esac

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "ERRO: pg_dump não está disponível no PATH." >&2
  exit 1
fi

dest_dir="${1:-backups}"
mkdir -p "${dest_dir}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
outfile="${dest_dir}/devolucao_${stamp}.dump"
partial="${outfile}.partial"

cleanup_partial() {
  status=$?
  if [[ "${status}" -ne 0 && -f "${partial}" ]]; then
    rm -f "${partial}"
    echo "ERRO: arquivo parcial desta execução removido. Backups anteriores foram preservados." >&2
  fi
  exit "${status}"
}
trap cleanup_partial EXIT

pg_dump \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file="${partial}" \
  --dbname="${DATABASE_URL}"

mv "${partial}" "${outfile}"
trap - EXIT
echo "Backup gravado: ${outfile}"
