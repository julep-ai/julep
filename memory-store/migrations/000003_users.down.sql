BEGIN;

-- Drop trigger first
DROP TRIGGER IF EXISTS update_users_updated_at ON users;

-- Drop indexes
DROP INDEX IF EXISTS users_metadata_gin_idx;

-- Drop foreign key constraint
ALTER TABLE IF EXISTS users
DROP CONSTRAINT IF EXISTS users_developer_id_fkey;

-- Finally drop the table
DROP TABLE IF EXISTS users;

COMMIT;
