-- Create transition type enum
CREATE TYPE transition_type AS ENUM (
    'init',
    'finish',
    'init_branch',
    'finish_branch',
    'wait',
    'resume',
    'error',
    'step',
    'cancelled'
);

-- Create transition cursor type
CREATE TYPE transition_cursor AS (
    workflow_name TEXT,
    step_index INT
);

-- Create transitions table
CREATE TABLE transitions (
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    execution_id UUID NOT NULL,
    transition_id UUID NOT NULL,
    type transition_type NOT NULL,
    step_definition JSONB NOT NULL,
    step_label TEXT DEFAULT NULL,
    current_step transition_cursor NOT NULL,
    next_step transition_cursor DEFAULT NULL,
    output JSONB,
    task_token TEXT DEFAULT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    CONSTRAINT pk_transitions PRIMARY KEY (created_at, execution_id, transition_id)
);

-- Convert to hypertable
SELECT create_hypertable('transitions', 'created_at');

-- Create unique constraint for current step
CREATE UNIQUE INDEX idx_transitions_current ON transitions (execution_id, current_step, created_at DESC);

-- Create unique constraint for next step (excluding nulls)
CREATE UNIQUE INDEX idx_transitions_next ON transitions (execution_id, next_step, created_at DESC) 
WHERE next_step IS NOT NULL;

-- Create unique constraint for step label (excluding nulls)
CREATE UNIQUE INDEX idx_transitions_label ON transitions (execution_id, step_label, created_at DESC) 
WHERE step_label IS NOT NULL;

-- Create sorted index on transition_id (optimized for UUID v7)
CREATE INDEX idx_transitions_transition_id_sorted ON transitions (transition_id DESC, created_at DESC);

-- Create sorted index on execution_id (optimized for UUID v7)
CREATE INDEX idx_transitions_execution_id_sorted ON transitions (execution_id DESC, created_at DESC);

-- Create a GIN index on the metadata column
CREATE INDEX idx_transitions_metadata ON transitions USING GIN (metadata);

-- Add foreign key constraint
ALTER TABLE transitions 
    ADD CONSTRAINT fk_transitions_execution
    FOREIGN KEY (execution_id)
    REFERENCES executions(execution_id);

-- Add comment to table
COMMENT ON TABLE transitions IS 'Stores transitions associated with AI agents for developers';