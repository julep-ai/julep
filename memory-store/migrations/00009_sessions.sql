-- Create sessions table
CREATE TABLE sessions (
    developer_id UUID NOT NULL,
    session_id UUID NOT NULL,
    situation TEXT,
    system_template TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    render_templates BOOLEAN NOT NULL DEFAULT true,
    token_budget INTEGER,
    context_overflow TEXT,
    forward_tool_calls BOOLEAN,
    recall_options JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT pk_sessions PRIMARY KEY (developer_id, session_id)
);

-- Create sorted index on session_id (optimized for UUID v7)
CREATE INDEX idx_sessions_id_sorted ON sessions (session_id DESC);

-- Create index for updated_at since we'll sort by it
CREATE INDEX idx_sessions_updated_at ON sessions (updated_at DESC);

-- Create foreign key constraint and index on developer_id
ALTER TABLE sessions 
    ADD CONSTRAINT fk_sessions_developer
    FOREIGN KEY (developer_id) 
    REFERENCES developers(developer_id);

CREATE INDEX idx_sessions_developer ON sessions (developer_id);

-- Create a GIN index on the metadata column
CREATE INDEX idx_sessions_metadata ON sessions USING GIN (metadata);

-- Create trigger to automatically update updated_at
CREATE TRIGGER trg_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment to table
COMMENT ON TABLE sessions IS 'Stores chat sessions and their configurations';

-- Create session_lookup table with participant type enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'participant_type') THEN
        CREATE TYPE participant_type AS ENUM ('user', 'agent');
    END IF;
END
$$;

-- Create session_lookup table without the CHECK constraint
CREATE TABLE session_lookup (
    developer_id UUID NOT NULL,
    session_id UUID NOT NULL,
    participant_type participant_type NOT NULL,
    participant_id UUID NOT NULL,
    PRIMARY KEY (developer_id, session_id, participant_type, participant_id),
    FOREIGN KEY (developer_id, session_id) REFERENCES sessions(developer_id, session_id)
);

-- Create indexes for common query patterns
CREATE INDEX idx_session_lookup_by_session ON session_lookup (developer_id, session_id);
CREATE INDEX idx_session_lookup_by_participant ON session_lookup (developer_id, participant_id);

-- Add comments to the table
COMMENT ON TABLE session_lookup IS 'Maps sessions to their participants (users and agents)';

-- Create trigger function to enforce conditional foreign keys
CREATE OR REPLACE FUNCTION validate_participant() RETURNS trigger AS $$
BEGIN
    IF NEW.participant_type = 'user' THEN
        PERFORM 1 FROM users WHERE developer_id = NEW.developer_id AND user_id = NEW.participant_id;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Invalid participant_id: % for participant_type user', NEW.participant_id;
        END IF;
    ELSIF NEW.participant_type = 'agent' THEN
        PERFORM 1 FROM agents WHERE developer_id = NEW.developer_id AND agent_id = NEW.participant_id;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Invalid participant_id: % for participant_type agent', NEW.participant_id;
        END IF;
    ELSE
        RAISE EXCEPTION 'Unknown participant_type: %', NEW.participant_type;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for INSERT and UPDATE operations
CREATE TRIGGER trg_validate_participant_before_insert
    BEFORE INSERT ON session_lookup
    FOR EACH ROW
    EXECUTE FUNCTION validate_participant();

CREATE TRIGGER trg_validate_participant_before_update
    BEFORE UPDATE ON session_lookup
    FOR EACH ROW
    EXECUTE FUNCTION validate_participant();