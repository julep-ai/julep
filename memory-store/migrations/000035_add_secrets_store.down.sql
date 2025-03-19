-- Drop indices first
DROP INDEX IF EXISTS idx_secrets_name;
DROP INDEX IF EXISTS idx_secrets_agent_id;
DROP INDEX IF EXISTS idx_secrets_developer_id;

-- Drop the secrets table
DROP TABLE IF EXISTS secrets;