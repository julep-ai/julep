BEGIN;

DROP FUNCTION IF EXISTS decrypt_secret;
DROP FUNCTION IF EXISTS encrypt_secret;
DROP TRIGGER IF EXISTS update_secrets_updated_at ON secrets;
DROP FUNCTION IF EXISTS update_secrets_updated_at;
DROP TABLE IF EXISTS secrets;

COMMIT; 