BEGIN;

-- Drop the usage table (this will also remove it from hypertables)
DO $$
BEGIN
    BEGIN
        DELETE FROM usage;
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during deleting all from usage: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DROP TABLE IF EXISTS usage;

COMMIT; 