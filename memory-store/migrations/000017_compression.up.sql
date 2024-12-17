/*
 * MULTI-DIMENSIONAL HYPERTABLES WITH COMPRESSION (Complexity: 8/10)
 * TimescaleDB's advanced feature that partitions data by both time (created_at) and space (session_id/execution_id).
 * Automatically compresses data older than 7 days to save storage while maintaining query performance.
 * Uses segment_by to group related rows and order_by to optimize decompression speed.
 */

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
