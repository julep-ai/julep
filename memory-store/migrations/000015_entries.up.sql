BEGIN;

-- Create chat_role enum
CREATE TYPE chat_role AS ENUM(
    'user',
    'assistant',
    'tool',
    'system',
    'developer'
);

-- Create a custom function that checks if `content` is non-empty
-- and that every JSONB element in the array is an 'object'.
CREATE
OR REPLACE FUNCTION all_jsonb_elements_are_objects (content jsonb[]) RETURNS boolean AS $$
DECLARE
    elem jsonb;
BEGIN
    -- Check each element in the `content` array
    FOREACH elem IN ARRAY content
    LOOP
        IF jsonb_typeof(elem) <> 'object' THEN
            RETURN false;
        END IF;
    END LOOP;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE TABLE IF NOT EXISTS entries (
    session_id UUID NOT NULL,
    entry_id UUID NOT NULL,
    source TEXT NOT NULL,
    role chat_role NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'message.create',
    name TEXT,
    content JSONB[] NOT NULL,
    tool_call_id TEXT DEFAULT NULL,
    tool_calls JSONB[] NOT NULL DEFAULT '{}'::JSONB[],
    model TEXT NOT NULL,
    token_count INTEGER DEFAULT NULL,
    tokenizer TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    timestamp DOUBLE PRECISION NOT NULL,
    CONSTRAINT pk_entries PRIMARY KEY (session_id, entry_id, created_at),
    CONSTRAINT ct_content_is_array_of_objects CHECK (all_jsonb_elements_are_objects (content)),
    CONSTRAINT ct_tool_calls_is_array_of_objects CHECK (all_jsonb_elements_are_objects (tool_calls))
);

-- Convert to hypertable if not already
SELECT
    create_hypertable (
        'entries',
        by_range ('created_at', INTERVAL '1 day'),
        if_not_exists => TRUE
    );

SELECT
    add_dimension (
        'entries',
        by_hash ('session_id', 2),
        if_not_exists => TRUE
    );

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_entries_by_session ON entries (session_id DESC);

-- Add foreign key constraint to sessions table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_entries_session'
    ) THEN
        ALTER TABLE entries
        ADD CONSTRAINT fk_entries_session
        FOREIGN KEY (session_id)
        REFERENCES sessions(session_id) ON DELETE CASCADE;
    END IF;
END $$;

-- TODO: We should consider using a timescale background job to update the token count
-- instead of a trigger.
-- https://docs.timescale.com/use-timescale/latest/user-defined-actions/create-and-register/
CREATE
OR REPLACE FUNCTION optimized_update_token_count_after () RETURNS TRIGGER AS $$
DECLARE
    calc_token_count INTEGER;
BEGIN
    -- Compute token_count outside the UPDATE statement for clarity and potential optimization
    calc_token_count := cardinality(
        ai.openai_tokenize(
            'gpt-4o', -- FIXME: Use `NEW.model`
            array_to_string(NEW.content::TEXT[], ' ')
        )
    );

    -- Perform the update only if token_count differs
    IF calc_token_count <> NEW.token_count THEN
        UPDATE entries
        SET token_count = calc_token_count
        WHERE entry_id = NEW.entry_id;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- FIXME: This trigger is causing the slow performance of the create_entries query
--
-- We should consider using a timescale background job to update the token count
-- instead of a trigger.
-- https://docs.timescale.com/use-timescale/latest/user-defined-actions/create-and-register/
--
-- CREATE TRIGGER trg_optimized_update_token_count_after
-- AFTER INSERT
-- OR
-- UPDATE ON entries FOR EACH ROW
-- EXECUTE FUNCTION optimized_update_token_count_after ();

-- Add trigger to update parent session's updated_at
CREATE
OR REPLACE FUNCTION update_session_updated_at () RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_session_updated_at
AFTER INSERT
OR
UPDATE ON entries FOR EACH ROW
EXECUTE FUNCTION update_session_updated_at ();

COMMIT;
