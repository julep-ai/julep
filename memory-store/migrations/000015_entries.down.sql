BEGIN;

-- Drop foreign key constraint if it exists
ALTER TABLE IF EXISTS entries
DROP CONSTRAINT IF EXISTS fk_entries_session;

-- Drop indexes
DROP INDEX IF EXISTS idx_entries_by_session;

-- Drop the hypertable (this will also drop the table)
DROP TABLE IF EXISTS entries;

-- Drop the enum type
DROP TYPE IF EXISTS chat_role;

COMMIT;
