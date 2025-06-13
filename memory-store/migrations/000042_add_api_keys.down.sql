BEGIN;

-- Drop helper functions
DROP FUNCTION IF EXISTS verify_api_key(TEXT, TEXT);
DROP FUNCTION IF EXISTS hash_api_key(TEXT);

-- Drop trigger and function
DROP TRIGGER IF EXISTS update_api_keys_timestamp_trigger ON api_keys;
DROP FUNCTION IF EXISTS update_api_keys_timestamp();

-- Drop table
DROP TABLE IF EXISTS api_keys CASCADE;

COMMIT; 