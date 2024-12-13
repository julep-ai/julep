-- Create tasks table
CREATE TABLE tasks (
    developer_id UUID NOT NULL,
    canonical_name CITEXT NOT NULL CONSTRAINT ct_tasks_canonical_name_length CHECK (length(canonical_name) >= 1 AND length(canonical_name) <= 255),
    agent_id UUID NOT NULL,
    task_id UUID NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL CONSTRAINT ct_tasks_name_length CHECK (length(name) >= 1 AND length(name) <= 255),
    description TEXT DEFAULT NULL CONSTRAINT ct_tasks_description_length CHECK (description IS NULL OR length(description) <= 1000),
    input_schema JSON NOT NULL,
    tools JSON[] DEFAULT ARRAY[]::JSON[],
    inherit_tools BOOLEAN DEFAULT FALSE,
    workflows JSON[] DEFAULT ARRAY[]::JSON[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::JSONB,
    CONSTRAINT pk_tasks PRIMARY KEY (developer_id, task_id),
    CONSTRAINT uq_tasks_canonical_name_unique UNIQUE (developer_id, canonical_name),
    CONSTRAINT fk_tasks_agent
        FOREIGN KEY (developer_id, agent_id)
        REFERENCES agents(developer_id, agent_id),
    CONSTRAINT ct_tasks_canonical_name_valid_identifier CHECK (canonical_name ~ '^[a-zA-Z][a-zA-Z0-9_]*$')
);

-- Create sorted index on task_id (optimized for UUID v7)
CREATE INDEX idx_tasks_id_sorted ON tasks (task_id DESC);

-- Create foreign key constraint and index on developer_id
CREATE INDEX idx_tasks_developer ON tasks (developer_id);

-- Create a GIN index on the entire metadata column
CREATE INDEX idx_tasks_metadata ON tasks USING GIN (metadata);

-- Create trigger to automatically update updated_at
CREATE TRIGGER trg_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment to table
COMMENT ON TABLE tasks IS 'Stores tasks associated with AI agents for developers';