#!/usr/bin/env bash

set -eo pipefail  # Exit on error
set -u  # Exit on undefined variable

# Ensure environment variables are set
if [ -z "$COZO_PORT" ] || [ -z "$COZO_AUTH_TOKEN" ]; then
    echo "COZO_PORT or COZO_AUTH_TOKEN is not set"
    exit 1
fi

COZO_BACKUP_DIR=${COZO_BACKUP_DIR:-/backup}
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
MAX_BACKUPS=${MAX_BACKUPS:-10}

curl -X POST \
    http://0.0.0.0:$COZO_PORT/backup \
    -H 'Content-Type: application/json' \
    -H "X-Cozo-Auth: ${COZO_AUTH_TOKEN}" \
    -d "{\"path\": \"${COZO_BACKUP_DIR}/cozo-backup-${TIMESTAMP}.bk\"}" \
    -w "\nStatus: %{http_code}\nResponse:\n" \
    -o /dev/stdout

# Print the number of backups
echo "Number of backups: $(ls -l ${COZO_BACKUP_DIR} | grep -c "cozo-backup-")"

# If the backup is successful, remove the oldest backup if the number of backups exceeds MAX_BACKUPS
if [ $(ls -l ${COZO_BACKUP_DIR} | grep -c "cozo-backup-") -gt $MAX_BACKUPS ]; then
    oldest_backup=$(ls -t ${COZO_BACKUP_DIR}/cozo-backup-*.bk | tail -n 1)

    if [ -n "$oldest_backup" ]; then
        rm "$oldest_backup"
        echo "Removed oldest backup: $oldest_backup"
    else
        echo "No backups found to remove"
    fi
fi