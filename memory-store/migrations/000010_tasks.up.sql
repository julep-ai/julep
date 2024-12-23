BEGIN;

/*
 * DEFERRED FOREIGN KEY CONSTRAINTS (Complexity: 6/10)
 * Uses PostgreSQL's deferred constraints to handle complex relationships between tasks and tools tables.
 * Constraints are checked at transaction commit rather than immediately, allowing circular references.
 * This enables more flexible data loading patterns while maintaining referential integrity.
 */
-- Create tasks table if it doesn't exist
CREATE TABLE IF NOT EXISTS tasks (
    developer_id UUID NOT NULL,
    canonical_name CITEXT NOT NULL CONSTRAINT ct_tasks_canonical_name_length CHECK (
        length(canonical_name) >= 1
        AND length(canonical_name) <= 255
    ),
    agent_id UUID NOT NULL,
    task_id UUID NOT NULL,
    "version" INTEGER NOT NULL DEFAULT 1,
    name TEXT NOT NULL CONSTRAINT ct_tasks_name_length CHECK (
        length(name) >= 1
        AND length(name) <= 255
    ),
    description TEXT DEFAULT NULL CONSTRAINT ct_tasks_description_length CHECK (
        description IS NULL
        OR length(description) <= 1000
    ),
    input_schema JSONB NOT NULL,
    inherit_tools BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::JSONB,
    CONSTRAINT pk_tasks PRIMARY KEY (developer_id, task_id, "version"),
    CONSTRAINT uq_tasks_canonical_name_unique UNIQUE (developer_id, canonical_name, "version"),
    CONSTRAINT fk_tasks_agent FOREIGN KEY (developer_id, agent_id) REFERENCES agents (developer_id, agent_id) ON DELETE CASCADE,
    CONSTRAINT ct_tasks_canonical_name_valid_identifier CHECK (canonical_name ~ '^[a-zA-Z][a-zA-Z0-9_]*$'),
    CONSTRAINT ct_tasks_metadata_is_object CHECK (jsonb_typeof(metadata) = 'object'),
    CONSTRAINT ct_tasks_input_schema_is_object CHECK (jsonb_typeof(input_schema) = 'object'),
    CONSTRAINT ct_tasks_version_positive CHECK ("version" > 0)
);

-- Create sorted index on task_id if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_tasks_id_sorted') THEN
        CREATE INDEX idx_tasks_id_sorted ON tasks (task_id DESC);
    END IF;
END $$;

-- Create index on canonical_name if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_tasks_canonical_name') THEN
        CREATE INDEX idx_tasks_canonical_name ON tasks (developer_id DESC, canonical_name);
    END IF;
END $$;

-- Create a GIN index on metadata if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_tasks_metadata') THEN
        CREATE INDEX idx_tasks_metadata ON tasks USING GIN (metadata);
    END IF;
END $$;

-- Create function to validate owner reference
CREATE OR REPLACE FUNCTION validate_tool_task()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.task_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM tasks
            WHERE developer_id = NEW.developer_id AND task_id = NEW.task_id
        ) THEN
            RAISE EXCEPTION 'Invalid task reference';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for validation
CREATE TRIGGER trg_validate_tool_task
BEFORE INSERT OR UPDATE ON tools
FOR EACH ROW
EXECUTE FUNCTION validate_tool_task();

-- Create updated_at trigger if it doesn't exist
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

-- Create 'workflows' table
CREATE TABLE IF NOT EXISTS workflows (
    developer_id UUID NOT NULL,
    task_id UUID NOT NULL,
    "version" INTEGER NOT NULL,
    name TEXT NOT NULL CONSTRAINT ct_workflows_name_length CHECK (
        length(name) >= 1
        AND length(name) <= 255
    ),
    step_idx INTEGER NOT NULL CONSTRAINT ct_workflows_step_idx_positive CHECK (step_idx >= 0),
    step_type TEXT NOT NULL CONSTRAINT ct_workflows_step_type_length CHECK (
        length(step_type) >= 1
        AND length(step_type) <= 255
    ),
    step_definition JSONB NOT NULL CONSTRAINT ct_workflows_step_definition_valid CHECK (jsonb_typeof(step_definition) = 'object'),
    CONSTRAINT pk_workflows PRIMARY KEY (developer_id, task_id, "version", name, step_idx),
    CONSTRAINT fk_workflows_tasks FOREIGN KEY (developer_id, task_id, "version") REFERENCES tasks (developer_id, task_id, "version") ON DELETE CASCADE
);

-- Add comment to 'workflows' table
COMMENT ON TABLE workflows IS 'Stores normalized workflows for tasks';

COMMIT;
