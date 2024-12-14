BEGIN;

-- Create tasks table if it doesn't exist
CREATE TABLE IF NOT EXISTS tasks (
    developer_id UUID NOT NULL,
    canonical_name CITEXT NOT NULL CONSTRAINT ct_tasks_canonical_name_length CHECK (length(canonical_name) >= 1 AND length(canonical_name) <= 255),
    agent_id UUID NOT NULL,
    task_id UUID NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL CONSTRAINT ct_tasks_name_length CHECK (length(name) >= 1 AND length(name) <= 255),
    description TEXT DEFAULT NULL CONSTRAINT ct_tasks_description_length CHECK (description IS NULL OR length(description) <= 1000),
    input_schema JSON NOT NULL,
    inherit_tools BOOLEAN DEFAULT FALSE,
    workflows JSON[] DEFAULT ARRAY[]::JSON[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::JSONB,
    CONSTRAINT pk_tasks PRIMARY KEY (developer_id, task_id),
    CONSTRAINT uq_tasks_canonical_name_unique UNIQUE (developer_id, canonical_name),
    CONSTRAINT uq_tasks_version_unique UNIQUE (task_id, version),
    CONSTRAINT fk_tasks_agent
        FOREIGN KEY (developer_id, agent_id)
        REFERENCES agents(developer_id, agent_id),
    CONSTRAINT ct_tasks_canonical_name_valid_identifier CHECK (canonical_name ~ '^[a-zA-Z][a-zA-Z0-9_]*$')
);

-- Create sorted index on task_id if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_tasks_id_sorted') THEN
        CREATE INDEX idx_tasks_id_sorted ON tasks (task_id DESC);
    END IF;
END $$;

-- Create index on developer_id if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_tasks_developer') THEN
        CREATE INDEX idx_tasks_developer ON tasks (developer_id);
    END IF;
END $$;

-- Create a GIN index on metadata if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_tasks_metadata') THEN
        CREATE INDEX idx_tasks_metadata ON tasks USING GIN (metadata);
    END IF;
END $$;

-- Add foreign key constraint if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_tools_task_id'
    ) THEN
        ALTER TABLE tools ADD CONSTRAINT fk_tools_task_id 
        FOREIGN KEY (task_id, task_version) REFERENCES tasks(task_id, version) 
        DEFERRABLE INITIALLY DEFERRED;
    END IF;
END $$;

-- Create trigger if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_trigger 
        WHERE tgname = 'trg_tasks_updated_at'
    ) THEN
        CREATE TRIGGER trg_tasks_updated_at
            BEFORE UPDATE ON tasks
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Add comment to table (comments are idempotent by default)
COMMENT ON TABLE tasks IS 'Stores tasks associated with AI agents for developers';

COMMIT;