-- Create table for storing secrets
CREATE TABLE secrets (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
    name VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    description TEXT DEFAULT NULL,
    developer_id UUID NOT NULL REFERENCES developers(id) ON DELETE CASCADE,
    agent_id UUID DEFAULT NULL REFERENCES agents(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE (name, developer_id, agent_id)
);

-- Add trigger for updated_at
CREATE TRIGGER set_secrets_updated_at
BEFORE UPDATE ON secrets
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- Add compression to secrets table 
SELECT alter_table_compression('secrets');

-- Add comments
COMMENT ON TABLE secrets IS 'Stores encrypted secrets for API keys and other sensitive data';
COMMENT ON COLUMN secrets.id IS 'Primary key for the secret';
COMMENT ON COLUMN secrets.created_at IS 'When the secret was created';
COMMENT ON COLUMN secrets.updated_at IS 'When the secret was last updated';
COMMENT ON COLUMN secrets.name IS 'Name of the secret (used for reference in templates)';
COMMENT ON COLUMN secrets.value IS 'Encrypted value of the secret';
COMMENT ON COLUMN secrets.description IS 'Optional description of what the secret is used for';
COMMENT ON COLUMN secrets.developer_id IS 'Reference to the developer that owns this secret';
COMMENT ON COLUMN secrets.agent_id IS 'Optional reference to an agent that can access this secret (NULL means developer-wide secret)';
COMMENT ON COLUMN secrets.metadata IS 'Additional metadata for the secret';

-- Add indices for faster lookups
CREATE INDEX idx_secrets_developer_id ON secrets(developer_id);
CREATE INDEX idx_secrets_agent_id ON secrets(agent_id) WHERE agent_id IS NOT NULL;
CREATE INDEX idx_secrets_name ON secrets(name);

-- Add pg_graphql settings
COMMENT ON TABLE secrets IS E'@graphql({"primary_key_columns": ["id"]})';