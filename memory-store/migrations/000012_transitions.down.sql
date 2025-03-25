BEGIN;

-- Drop foreign key constraint if exists
ALTER TABLE IF EXISTS transitions
DROP CONSTRAINT IF EXISTS fk_transitions_execution;

-- Drop indexes if they exist
DROP INDEX IF EXISTS idx_transitions_metadata;

DROP INDEX IF EXISTS idx_transitions_label;

DROP INDEX IF EXISTS idx_transitions_next;

DROP INDEX IF EXISTS idx_transitions_current;

DROP INDEX IF EXISTS transitions_created_at_idx;

-- Drop the transitions table (this will also remove it from hypertables)
DO $$
BEGIN
    BEGIN
        DELETE FROM transitions;
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during deleting all from transitions: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DROP TABLE IF EXISTS transitions;

-- Drop custom types if they exist
DROP TYPE IF EXISTS transition_cursor;

DROP TYPE IF EXISTS transition_type;

-- Drop the trigger and function for transition validation
DROP TRIGGER IF EXISTS validate_transition ON transitions;

DROP FUNCTION IF EXISTS check_valid_transition ();

COMMIT;
