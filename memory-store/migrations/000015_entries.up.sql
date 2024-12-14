BEGIN;

-- Create chat_role enum
CREATE TYPE chat_role AS ENUM('user', 'assistant', 'tool', 'system');

-- Create entries table
CREATE TABLE IF NOT EXISTS entries (
    session_id UUID NOT NULL,
    entry_id UUID NOT NULL,
    source TEXT NOT NULL,
    role chat_role NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'message.create',
    name TEXT,
    content JSONB[] NOT NULL,
    tool_call_id TEXT DEFAULT NULL,
    tool_calls JSONB[] NOT NULL DEFAULT '{}',
    token_count INTEGER NOT NULL,
    model TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_entries PRIMARY KEY (session_id, entry_id, created_at)
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
CREATE INDEX IF NOT EXISTS idx_entries_by_session ON entries (session_id DESC, entry_id DESC);

-- Add foreign key constraint to sessions table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_entries_session'
    ) THEN
        ALTER TABLE entries
        ADD CONSTRAINT fk_entries_session
        FOREIGN KEY (session_id)
        REFERENCES sessions(session_id);
    END IF;
END $$;

COMMIT;