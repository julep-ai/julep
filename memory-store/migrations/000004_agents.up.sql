BEGIN;

-- Drop existing objects if they exist
DROP TRIGGER IF EXISTS trg_agents_updated_at ON agents;

DROP INDEX IF EXISTS idx_agents_metadata;

DROP INDEX IF EXISTS idx_agents_developer;

DROP INDEX IF EXISTS idx_agents_id_sorted;

DROP TABLE IF EXISTS agents;

-- Create agents table
CREATE TABLE IF NOT EXISTS agents (
    developer_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    canonical_name citext NOT NULL CONSTRAINT ct_agents_canonical_name_length CHECK (
        length(canonical_name) >= 1
        AND length(canonical_name) <= 255
    ),
    name TEXT NOT NULL CONSTRAINT ct_agents_name_length CHECK (
        length(name) >= 1
        AND length(name) <= 255
    ),
    about TEXT CONSTRAINT ct_agents_about_length CHECK (
        about IS NULL
        OR length(about) <= 1000
    ),
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

-- Create foreign key constraint and index on developer_id
ALTER TABLE agents
DROP CONSTRAINT IF EXISTS fk_agents_developer,
ADD CONSTRAINT fk_agents_developer FOREIGN KEY (developer_id) REFERENCES developers (developer_id);

-- Create a GIN index on the entire metadata column
CREATE INDEX IF NOT EXISTS idx_agents_metadata ON agents USING GIN (metadata);

-- Create trigger to automatically update updated_at
CREATE
OR REPLACE TRIGGER trg_agents_updated_at BEFORE
UPDATE ON agents FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column ();

-- Add comment to table
COMMENT ON TABLE agents IS 'Stores AI agent configurations and metadata for developers';

COMMIT;