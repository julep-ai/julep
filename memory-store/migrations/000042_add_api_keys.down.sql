BEGIN;

-- Drop helper functions (now using RETURNS TABLE syntax)
DROP FUNCTION IF EXISTS decrypt_api_key(BYTEA, TEXT);
DROP FUNCTION IF EXISTS encrypt_api_key(TEXT, TEXT);

-- Drop trigger and function
DROP TRIGGER IF EXISTS update_api_keys_timestamp_trigger ON api_keys;
DROP FUNCTION IF EXISTS update_api_keys_timestamp();

-- Drop table
DROP TABLE IF EXISTS api_keys CASCADE;

COMMIT; 