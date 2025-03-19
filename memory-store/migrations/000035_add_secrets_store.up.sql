BEGIN;

-- Create table for storing secrets
CREATE TABLE secrets (
    secret_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
    name VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    description TEXT DEFAULT NULL,
    developer_id UUID NOT NULL REFERENCES developers(developer_id) ON DELETE CASCADE,
    agent_id UUID DEFAULT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT fk_secrets_agent FOREIGN KEY (developer_id, agent_id)
        REFERENCES agents(developer_id, agent_id) ON DELETE CASCADE,
    UNIQUE (name, developer_id, agent_id)
);

-- Add trigger for updated_at
CREATE TRIGGER set_secrets_updated_at
BEFORE UPDATE ON secrets
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Add indices for faster lookups
CREATE INDEX idx_secrets_developer_id ON secrets(developer_id);
CREATE INDEX idx_secrets_agent_id ON secrets(agent_id) WHERE agent_id IS NOT NULL;
CREATE INDEX idx_secrets_name ON secrets(name);

COMMIT;
