#!/usr/bin/env bash

set -eo pipefail

# Create mount directory for service and RocksDB directory
mkdir -p ${COZO_MNT_DIR:=/data}/${COZO_ROCKSDB_DIR:-cozo.db}

# Create auth token if not exists.
export COZO_AUTH_TOKEN=${COZO_AUTH_TOKEN:=`tr -dc A-Za-z0-9 </dev/urandom | head -c 72`}
echo "Auth token: $COZO_AUTH_TOKEN"
export COZO_ROCKSDB_DIR=${COZO_ROCKSDB_DIR:-cozo.db}
echo $COZO_AUTH_TOKEN > $COZO_MNT_DIR/${COZO_ROCKSDB_DIR}.newrocksdb.cozo_auth

# Copy options file to the RocksDB directory
cp /app/options $COZO_MNT_DIR/${COZO_ROCKSDB_DIR}/OPTIONS-000007

# Start server
${APP_HOME:=.}/bin/cozo server \
    --engine newrocksdb \
    --path $COZO_MNT_DIR/${COZO_ROCKSDB_DIR} \
    --bind 0.0.0.0 \
    --port ${COZO_PORT:=9070} \
    -c '{"enable_write_buffer_manager": true, "allow_stall": true, "lru_cache_mb": 4096, "write_buffer_mb": 4096}'
