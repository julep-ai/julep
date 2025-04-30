BEGIN;

DROP FUNCTION IF EXISTS decrypt_secret;
DROP FUNCTION IF EXISTS encrypt_secret;
DROP INDEX IF EXISTS idx_secrets_metadata;
DROP INDEX IF EXISTS idx_secrets_name;
DROP INDEX IF EXISTS idx_secrets_developer_id;
DROP TABLE IF EXISTS secrets;

COMMIT; 