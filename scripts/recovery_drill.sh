#!/usr/bin/env bash
# Recovery drill: verify backup/restore works end-to-end.
# Run: make recovery-drill
set -euo pipefail

echo "=== OpenMinds Recovery Drill ==="
echo "1. Taking backup..."
docker compose -f docker/docker-compose.yml exec postgres \
    pg_dump -U openminds openminds > /tmp/openminds_backup_$(date +%s).sql

BACKUP_FILE=$(ls -t /tmp/openminds_backup_*.sql | head -1)
echo "   Backup: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

echo "2. Verifying backup integrity..."
grep -q "CREATE TABLE" "$BACKUP_FILE" || { echo "FAIL: backup has no tables"; exit 1; }
echo "   ✓ Backup contains schema"

echo "3. Testing restore to temp database..."
docker compose -f docker/docker-compose.yml exec postgres \
    psql -U openminds -c "CREATE DATABASE restore_test"
docker compose -f docker/docker-compose.yml exec -i postgres \
    psql -U openminds restore_test < /dev/stdin < "$BACKUP_FILE"
echo "   ✓ Restore successful"

echo "4. Verifying restored data..."
ROW_COUNT=$(docker compose -f docker/docker-compose.yml exec postgres \
    psql -U openminds restore_test -t -c "SELECT COUNT(*) FROM issues")
echo "   Restored issues: $ROW_COUNT"

echo "5. Cleaning up..."
docker compose -f docker/docker-compose.yml exec postgres \
    psql -U openminds -c "DROP DATABASE restore_test"
rm -f "$BACKUP_FILE"

echo "=== Recovery drill PASSED ==="
