BEGIN;

-- Drop agent_files table and its dependencies
DROP TABLE IF EXISTS agent_files;

-- Drop user_files table and its dependencies
DROP TABLE IF EXISTS user_files;

-- Drop files table and its dependencies
DROP TRIGGER IF EXISTS trg_files_updated_at ON files;

DROP TABLE IF EXISTS files;

COMMIT;
