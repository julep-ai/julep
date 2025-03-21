BEGIN;

DO $$
BEGIN
    BEGIN
        ALTER TABLE entries
            SET (
                timescaledb.compress = TRUE,
                timescaledb.compress_segmentby = 'session_id',
                timescaledb.compress_orderby = 'created_at DESC, entry_id DESC',
                timescaledb.compress_chunk_time_interval = '28 days'
            );
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during entries.compress: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DO $$
BEGIN
    BEGIN
        SELECT
            add_compression_policy ('entries', INTERVAL '7 days');
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during add_compression_policy(entries): %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DO $$
BEGIN
    BEGIN
        ALTER TABLE transitions
        SET
            (
                timescaledb.compress = TRUE,
                timescaledb.compress_segmentby = 'execution_id',
                timescaledb.compress_orderby = 'created_at DESC, transition_id DESC',
                timescaledb.compress_chunk_time_interval = '28 days'
            );
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during transitions.compress: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DO $$
BEGIN
    BEGIN
        SELECT
            add_compression_policy ('transitions', INTERVAL '7 days');
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during add_compression_policy(transitions): %, %', SQLSTATE, SQLERRM;
    END;
END $$;

COMMIT;