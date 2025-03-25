BEGIN;

/*
 * CUSTOM TYPES AND ENUMS WITH COMPLEX CONSTRAINTS (Complexity: 7/10)
 * Creates custom composite type transition_cursor to track workflow state and enum type for transition states.
 * Uses compound primary key combining timestamps and UUIDs for efficient time-series operations.
 * Implements complex indexing strategy optimized for various query patterns (current state, next state, labels).
 */

-- Create transition type enum if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transition_type') THEN
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
    END IF;
END $$;

-- Create transition cursor type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transition_cursor') THEN
        CREATE TYPE transition_cursor AS (
            workflow_name TEXT,
            step_index INT
        );
    END IF;
END $$;

-- Create transitions table if it doesn't exist
CREATE TABLE IF NOT EXISTS transitions (
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    execution_id UUID NOT NULL,
    transition_id UUID NOT NULL,
    type transition_type NOT NULL,
    step_label TEXT DEFAULT NULL,
    current_step transition_cursor NOT NULL,
    next_step transition_cursor DEFAULT NULL,
    output JSONB,
    task_token TEXT DEFAULT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    CONSTRAINT pk_transitions PRIMARY KEY (created_at, execution_id, transition_id),
    CONSTRAINT ct_metadata_is_object CHECK (jsonb_typeof(metadata) = 'object')
);

-- Convert to hypertable if not already
SELECT
    create_hypertable (
        'transitions',
        by_range ('created_at', INTERVAL '1 day'),
        if_not_exists => TRUE
    );

SELECT
    add_dimension (
        'transitions',
        by_hash ('execution_id', 2),
        if_not_exists => TRUE
    );

-- Create indexes if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_transitions_metadata') THEN
        CREATE INDEX idx_transitions_metadata ON transitions USING GIN (metadata);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_transitions_label') THEN
        CREATE UNIQUE INDEX idx_transitions_label ON transitions USING btree (execution_id, step_label, created_at DESC)
        WHERE (step_label IS NOT NULL);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_transitions_next') THEN
        CREATE UNIQUE INDEX idx_transitions_next ON transitions USING btree (execution_id, next_step, created_at DESC)
        WHERE (next_step IS NOT NULL);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_transitions_current') THEN
        CREATE UNIQUE INDEX idx_transitions_current ON transitions USING btree (execution_id, current_step, created_at DESC)
    END IF;
END $$;


-- Add foreign key constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_transitions_execution') THEN
        ALTER TABLE transitions
            ADD CONSTRAINT fk_transitions_execution
            FOREIGN KEY (execution_id)
            REFERENCES executions(execution_id)
            ON DELETE CASCADE;
    END IF;
END $$;

-- Add comment to table
COMMENT ON TABLE transitions IS 'Stores transitions associated with AI agents for developers';

-- Create a trigger function that checks for valid transitions
CREATE
OR REPLACE FUNCTION check_valid_transition () RETURNS trigger AS $$
DECLARE
    previous_type transition_type;
    valid_next_types transition_type[];
BEGIN
    -- Get the latest transition_type for this execution_id
    SELECT t.type INTO previous_type
    FROM transitions t
    WHERE t.execution_id = NEW.execution_id
    ORDER BY t.created_at DESC
    LIMIT 1;

    IF previous_type IS NULL THEN
        -- If there is no previous transition, allow only 'init' or 'init_branch'
        IF NEW.type NOT IN ('init', 'init_branch', 'error', 'cancelled') THEN
            RAISE EXCEPTION 'First transition must be init / init_branch / error / cancelled, got %', NEW.type;
        END IF;
    ELSE
        -- Define the valid_next_types array based on previous_type
        CASE previous_type
            WHEN 'init' THEN
                valid_next_types := ARRAY['wait', 'error', 'step', 'cancelled', 'init_branch', 'finish'];
            WHEN 'init_branch' THEN
                valid_next_types := ARRAY['wait', 'error', 'step', 'cancelled', 'init_branch', 'finish_branch', 'finish'];
            WHEN 'wait' THEN
                valid_next_types := ARRAY['resume', 'step', 'cancelled', 'finish', 'finish_branch'];
            WHEN 'resume' THEN
                valid_next_types := ARRAY['wait', 'error', 'cancelled', 'step', 'finish', 'finish_branch', 'init_branch'];
            WHEN 'step' THEN
                valid_next_types := ARRAY['wait', 'error', 'cancelled', 'step', 'finish', 'finish_branch', 'init_branch'];
            WHEN 'finish_branch' THEN
                valid_next_types := ARRAY['wait', 'error', 'cancelled', 'step', 'finish', 'init_branch', 'finish_branch'];
            WHEN 'finish' THEN
                valid_next_types := ARRAY[]::transition_type[];  -- No valid next transitions
            WHEN 'error' THEN
                valid_next_types := ARRAY[]::transition_type[];  -- No valid next transitions
            WHEN 'cancelled' THEN
                valid_next_types := ARRAY[]::transition_type[];  -- No valid next transitions
            ELSE
                RAISE EXCEPTION 'Unknown previous transition type: %', previous_type;
        END CASE;

        IF NOT NEW.type = ANY(valid_next_types) THEN
            RAISE EXCEPTION 'Invalid transition from % to %', previous_type, NEW.type;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger on the transitions table
CREATE OR REPLACE TRIGGER validate_transition BEFORE INSERT ON transitions FOR EACH ROW
EXECUTE FUNCTION check_valid_transition ();

COMMIT;
