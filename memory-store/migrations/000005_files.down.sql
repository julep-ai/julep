BEGIN;

-- Drop file_owners table and its dependencies
DROP TRIGGER IF EXISTS trg_validate_file_owner ON file_owners;
DROP FUNCTION IF EXISTS validate_file_owner();
DROP TABLE IF EXISTS file_owners;

-- Drop files table and its dependencies
DROP TRIGGER IF EXISTS trg_files_updated_at ON files;
DROP TABLE IF EXISTS files;

COMMIT;
