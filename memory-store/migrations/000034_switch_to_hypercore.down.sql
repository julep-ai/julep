BEGIN;

ALTER MATERIALIZED VIEW latest_transitions
    SET (
        timescaledb.enable_columnstore = false
    );

-- Drop the index on execution_id
DROP INDEX IF EXISTS idx_transitions_execution_id_hash;

-- Entries: Revert hypercore changes
CALL remove_columnstore_policy('entries', if_exists => true);

ALTER TABLE
    entries
SET ACCESS METHOD heap;
DO $$
BEGIN
    BEGIN
        ALTER TABLE
            entries
        SET
            (
                timescaledb.enable_columnstore = false
            );
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred disabling columnstore for entries: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DO $$
BEGIN
    BEGIN
        ALTER TABLE
            entries 
        SET
            (
                timescaledb.compress
            );
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred setting compression for entries: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

-- Transitions: Revert hypercore changes
CALL remove_columnstore_policy('transitions', if_exists => true);

ALTER TABLE
    transitions
SET
    ACCESS METHOD heap;

DO $$
BEGIN
    BEGIN
        ALTER TABLE
            transitions
        SET
            (
                timescaledb.enable_columnstore = false
            );
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred disabling columnstore for transitions: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DO $$
BEGIN
    BEGIN
        ALTER TABLE
            transitions 
        SET
            (
                timescaledb.compress
            );
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred setting compression for transitions: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

COMMIT;