BEGIN;

-- Drop functions first
DROP FUNCTION IF EXISTS verify_api_key;
DROP FUNCTION IF EXISTS encrypt_api_key;

-- Drop api_keys table
DROP TABLE IF EXISTS api_keys;

COMMIT; 