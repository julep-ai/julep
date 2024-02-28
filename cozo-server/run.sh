#!/usr/bin/env bash

set -eo pipefail

# Create mount directory for service.
mkdir -p ${MNT_DIR:=./tmp}

# Create auth token if not exists.
export COZO_AUTH_TOKEN=${COZO_AUTH_TOKEN:=`tr -dc A-Za-z0-9 </dev/urandom | head -c 72`}
echo "Auth token: $COZO_AUTH_TOKEN"
export COZO_ROCKSDB_FILE=${COZO_ROCKSDB_FILE:-cozo.db}
echo $COZO_AUTH_TOKEN > $MNT_DIR/${COZO_ROCKSDB_FILE}.rocksdb.cozo_auth

# Start server
${APP_HOME:=.}/bin/cozo-bin server \
    --engine rocksdb \
    --path $MNT_DIR/${COZO_ROCKSDB_FILE} \
    --bind 0.0.0.0 \
    --port ${PORT:=9070} \
    --token-table __tokens
