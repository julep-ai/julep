BEGIN;

ALTER TABLE entries
SET
    (
        timescaledb.compress = TRUE,
        timescaledb.compress_segmentby = 'session_id',
        timescaledb.compress_orderby = 'created_at DESC, entry_id DESC'
    );

SELECT
    add_compression_policy ('entries', INTERVAL '7 days');

ALTER TABLE transitions
SET
    (
        timescaledb.compress = TRUE,
        timescaledb.compress_segmentby = 'execution_id',
        timescaledb.compress_orderby = 'created_at DESC, transition_id DESC'
    );

SELECT
    add_compression_policy ('transitions', INTERVAL '7 days');

COMMIT;
