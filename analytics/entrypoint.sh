#!/bin/bash
set -e

# Set environment variables for database initialization
export POSTGRES_HOST="${MB_DB_HOST}"
export POSTGRES_USER="${MB_DB_USER}"
export POSTGRES_PASSWORD="${MB_DB_PASS}"

# Run database initialization
/app/init-metabase-db.sh

# Start Metabase
exec /app/run_metabase.sh

# AIDEV-NOTE: Custom entrypoint ensures database exists before Metabase starts