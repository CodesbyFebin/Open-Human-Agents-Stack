#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%Y%m%d-%H%M%S)
OUT="${1:-./backups/openminds-$STAMP.sql}"
mkdir -p "$(dirname "$OUT")"
pg_dump "${DATABASE_URL:-postgresql://openminds:openminds@localhost:5432/openminds}" > "$OUT"
echo "backup written: $OUT"
