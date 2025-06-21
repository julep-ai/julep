BEGIN;

-- Drop helper functions (updated signatures due to composite type returns)
DROP FUNCTION IF EXISTS decrypt_api_key(BYTEA, TEXT);
DROP FUNCTION IF EXISTS encrypt_api_key(TEXT, TEXT);

-- Drop composite types
DROP TYPE IF EXISTS decrypted_api_key_result;
DROP TYPE IF EXISTS encrypted_api_key_result;

-- Drop trigger and function
DROP TRIGGER IF EXISTS update_api_keys_timestamp_trigger ON api_keys;
DROP FUNCTION IF EXISTS update_api_keys_timestamp();

-- Drop table
DROP TABLE IF EXISTS api_keys CASCADE;

COMMIT; 