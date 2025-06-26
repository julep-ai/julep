BEGIN;

-- Drop trigger for automatically updating 'updated_at'
DROP TRIGGER IF EXISTS update_secrets_timestamp_trigger ON secrets;
-- Drop trigger function for automatically updating 'updated_at'
DROP FUNCTION IF EXISTS update_secrets_timestamp();
-- Drop encryption/decryption functions
DROP FUNCTION IF EXISTS decrypt_secret;
DROP FUNCTION IF EXISTS encrypt_secret;
DROP INDEX IF EXISTS idx_secrets_metadata;
DROP INDEX IF EXISTS idx_secrets_name;
DROP INDEX IF EXISTS idx_secrets_developer_id;
DROP TABLE IF EXISTS secrets;

COMMIT; 