BEGIN;

-- Create executions table if it doesn't exist
CREATE TABLE IF NOT EXISTS executions (
    developer_id UUID NOT NULL,
    task_id UUID NOT NULL,
    task_version INTEGER NOT NULL,
    execution_id UUID NOT NULL,
    input JSONB NOT NULL,
    -- NOTE: These will be generated using continuous aggregates from transitions
    -- status TEXT DEFAULT 'pending',
    -- output JSONB DEFAULT NULL,
    -- error TEXT DEFAULT NULL,
    -- updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_executions PRIMARY KEY (execution_id),
    CONSTRAINT fk_executions_developer FOREIGN KEY (developer_id) REFERENCES developers (developer_id),
    CONSTRAINT fk_executions_task FOREIGN KEY (developer_id, task_id) REFERENCES tasks (developer_id, task_id)
);

-- Create sorted index on execution_id (optimized for UUID v7)
CREATE INDEX IF NOT EXISTS idx_executions_execution_id_sorted ON executions (execution_id DESC);

-- Create index on developer_id
CREATE INDEX IF NOT EXISTS idx_executions_developer_id ON executions (developer_id);

-- Create index on task_id
CREATE INDEX IF NOT EXISTS idx_executions_task_id ON executions (task_id);

-- Create a GIN index on the metadata column
CREATE INDEX IF NOT EXISTS idx_executions_metadata ON executions USING GIN (metadata);

-- Add comment to table (comments are idempotent by default)
COMMENT ON TABLE executions IS 'Stores executions associated with AI agents for developers';

COMMIT;