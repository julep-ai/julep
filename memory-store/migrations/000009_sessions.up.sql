BEGIN;

-- Create sessions table if it doesn't exist
CREATE TABLE IF NOT EXISTS sessions (
    developer_id UUID NOT NULL,
    session_id UUID NOT NULL,
    situation TEXT,
    system_template TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- TODO: Derived from entries
    -- updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    render_templates BOOLEAN NOT NULL DEFAULT true,
    token_budget INTEGER,
    context_overflow TEXT,
    forward_tool_calls BOOLEAN,
    recall_options JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT pk_sessions PRIMARY KEY (developer_id, session_id)
);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_sessions_id_sorted ON sessions (session_id DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_metadata ON sessions USING GIN (metadata);

-- Create foreign key if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_sessions_developer'
    ) THEN
        ALTER TABLE sessions 
        ADD CONSTRAINT fk_sessions_developer
        FOREIGN KEY (developer_id) 
        REFERENCES developers(developer_id);
    END IF;
END $$;

-- Create trigger if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_sessions_updated_at'
    ) THEN
        CREATE TRIGGER trg_sessions_updated_at
        BEFORE UPDATE ON sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Create participant_type enum if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'participant_type') THEN
        CREATE TYPE participant_type AS ENUM ('user', 'agent');
    END IF;
END $$;

-- Create session_lookup table if it doesn't exist
CREATE TABLE IF NOT EXISTS session_lookup (
    developer_id UUID NOT NULL,
    session_id UUID NOT NULL,
    participant_type participant_type NOT NULL,
    participant_id UUID NOT NULL,
    PRIMARY KEY (developer_id, session_id, participant_type, participant_id),
    FOREIGN KEY (developer_id, session_id) REFERENCES sessions(developer_id, session_id)
);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_session_lookup_by_session ON session_lookup (developer_id, session_id);
CREATE INDEX IF NOT EXISTS idx_session_lookup_by_participant ON session_lookup (developer_id, participant_id);

-- Create or replace the validation function
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

-- Create triggers if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_validate_participant_before_insert'
    ) THEN
        CREATE TRIGGER trg_validate_participant_before_insert
        BEFORE INSERT ON session_lookup
        FOR EACH ROW
        EXECUTE FUNCTION validate_participant();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_validate_participant_before_update'
    ) THEN
        CREATE TRIGGER trg_validate_participant_before_update
        BEFORE UPDATE ON session_lookup
        FOR EACH ROW
        EXECUTE FUNCTION validate_participant();
    END IF;
END $$;

COMMIT;