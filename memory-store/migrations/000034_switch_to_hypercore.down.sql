BEGIN;

DO $$
BEGIN
    BEGIN
        SELECT
            remove_compression_policy ('entries');
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during remove_compression_policy(entries): %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DO $$
BEGIN
    BEGIN
        SELECT
            remove_compression_policy ('transitions');
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during remove_compression_policy(transitions): %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DO $$
BEGIN
    BEGIN
        ALTER TABLE entries
        SET
            (timescaledb.compress = FALSE);
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during unsetting entries.compress: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DO $$
BEGIN
    BEGIN
        ALTER TABLE transitions
        SET
            (timescaledb.compress = FALSE);
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during unsetting transitions.compress: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

COMMIT;