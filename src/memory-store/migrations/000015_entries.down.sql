BEGIN;

DROP TRIGGER IF EXISTS trg_optimized_update_token_count_after ON entries;

DROP FUNCTION IF EXISTS optimized_update_token_count_after;

-- Drop foreign key constraint if it exists
ALTER TABLE IF EXISTS entries
DROP CONSTRAINT IF EXISTS fk_entries_session;

-- Drop indexes
DROP INDEX IF EXISTS idx_entries_by_session;

-- Drop the hypertable (this will also drop the table)
DROP TABLE IF EXISTS entries;

-- Drop the function
DROP FUNCTION IF EXISTS all_jsonb_elements_are_objects;

-- Drop the enum type
DROP TYPE IF EXISTS chat_role;

COMMIT;