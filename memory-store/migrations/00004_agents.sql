-- Create agents table
CREATE TABLE agents (
    developer_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    canonical_name citext NOT NULL CONSTRAINT ct_agents_canonical_name_length CHECK (length(canonical_name) >= 1 AND length(canonical_name) <= 255),
    name TEXT NOT NULL CONSTRAINT ct_agents_name_length CHECK (length(name) >= 1 AND length(name) <= 255),
    about TEXT CONSTRAINT ct_agents_about_length CHECK (about IS NULL OR length(about) <= 1000),
    instructions TEXT[] DEFAULT ARRAY[]::TEXT[],
    model TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    default_settings JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT pk_agents PRIMARY KEY (developer_id, agent_id),
    CONSTRAINT uq_agents_canonical_name_unique UNIQUE (developer_id, canonical_name), -- per developer
    CONSTRAINT ct_agents_canonical_name_valid_identifier CHECK (canonical_name ~ '^[a-zA-Z][a-zA-Z0-9_]*$')
);

-- Create sorted index on agent_id (optimized for UUID v7)
CREATE INDEX idx_agents_id_sorted ON agents (agent_id DESC);

-- Create foreign key constraint and index on developer_id
ALTER TABLE agents 
    ADD CONSTRAINT fk_agents_developer
    FOREIGN KEY (developer_id) 
    REFERENCES developers(developer_id);

CREATE INDEX idx_agents_developer ON agents (developer_id);

-- Create a GIN index on the entire metadata column
CREATE INDEX idx_agents_metadata ON agents USING GIN (metadata);

-- Create trigger to automatically update updated_at
CREATE TRIGGER trg_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment to table
COMMENT ON TABLE agents IS 'Stores AI agent configurations and metadata for developers';