#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - checking if metabase database exists"

# Check if metabase database exists
if ! PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw metabase; then
    echo "Creating metabase database..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE metabase;
        GRANT ALL PRIVILEGES ON DATABASE metabase TO $POSTGRES_USER;
EOSQL
    echo "Metabase database created successfully"
else
    echo "Metabase database already exists"
fi

# AIDEV-NOTE: Script ensures metabase database exists before Metabase starts