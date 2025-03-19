BEGIN;

-- -- Make sure all extensions are up to date
-- ALTER EXTENSION timescaledb UPDATE;
-- ALTER EXTENSION vectorscale UPDATE;
-- ALTER EXTENSION ai UPDATE;

-- Entries: Switch to hypercore
SELECT remove_compression_policy ('entries', if_exists => true);

ALTER TABLE
    entries
SET
    (
        timescaledb.enable_columnstore,
        timescaledb.segmentby = 'session_id',
        timescaledb.compress_chunk_time_interval = '14 days'
    ),
SET
    ACCESS METHOD hypercore;

CALL add_columnstore_policy(
    'entries',
    after => interval '7 days',
    if_not_exists => true,
    hypercore_use_access_method => true
);


-- Transitions: Switch to hypercore
SELECT remove_compression_policy ('transitions', if_exists => true);

ALTER TABLE
    transitions
SET
    (
        timescaledb.enable_columnstore = true,
        timescaledb.segmentby = 'execution_id',
        timescaledb.orderby = 'created_at DESC',
        timescaledb.compress_chunk_time_interval = '14 days'
    ),
SET
    ACCESS METHOD hypercore;

CALL add_columnstore_policy(
    'transitions',
    after => interval '7 days',
    if_not_exists => true,
    hypercore_use_access_method => true
);

CREATE INDEX IF NOT EXISTS idx_transitions_execution_id_hash ON transitions USING hash (execution_id);

ALTER MATERIALIZED VIEW latest_transitions
    SET (
        timescaledb.enable_columnstore = true,
        timescaledb.orderby = 'bucket DESC',
        timescaledb.segmentby = 'execution_id',
        timescaledb.compress_chunk_time_interval = '14 days'
    );

COMMIT;