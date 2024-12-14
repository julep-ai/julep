BEGIN;

-- Create temporal_executions_lookup table
CREATE TABLE
    IF NOT EXISTS temporal_executions_lookup (
        execution_id UUID NOT NULL,
        id TEXT NOT NULL,
        run_id TEXT,
        first_execution_run_id TEXT,
        result_run_id TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT pk_temporal_executions_lookup PRIMARY KEY (execution_id, id),
        CONSTRAINT fk_temporal_executions_lookup_execution FOREIGN KEY (execution_id) REFERENCES executions (execution_id)
    );

-- Create sorted index on execution_id (optimized for UUID v7)
CREATE INDEX IF NOT EXISTS idx_temporal_executions_lookup_execution_id_sorted ON temporal_executions_lookup (execution_id DESC);

-- Add comment to table
COMMENT ON TABLE temporal_executions_lookup IS 'Stores temporal workflow execution lookup data for AI agent executions';

COMMIT;