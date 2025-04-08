BEGIN;

DROP FUNCTION IF EXISTS decrypt_secret;
DROP FUNCTION IF EXISTS encrypt_secret;
DROP TRIGGER IF EXISTS trg_secrets_updated_at ON secrets;
DROP TABLE IF EXISTS secrets;

COMMIT; 