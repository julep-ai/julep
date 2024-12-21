BEGIN;

-- Create files table
CREATE TABLE IF NOT EXISTS files (
    developer_id UUID NOT NULL,
    file_id UUID NOT NULL,
    name TEXT NOT NULL CONSTRAINT ct_files_name_length CHECK (
        length(name) >= 1
        AND length(name) <= 255
    ),
    description TEXT DEFAULT NULL CONSTRAINT ct_files_description_length CHECK (
        description IS NULL
        OR length(description) <= 1000
    ),
    mime_type TEXT DEFAULT NULL CONSTRAINT ct_files_mime_type_length CHECK (
        mime_type IS NULL
        OR length(mime_type) <= 127
    ),
    size BIGINT NOT NULL CONSTRAINT ct_files_size_positive CHECK (size > 0),
    hash BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_files PRIMARY KEY (developer_id, file_id)
);

-- Create foreign key constraint and index if they don't exist
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_files_developer') THEN
        ALTER TABLE files
            ADD CONSTRAINT fk_files_developer
            FOREIGN KEY (developer_id)
            REFERENCES developers(developer_id);
    END IF;
END $$;

-- Create trigger if it doesn't exist
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_files_updated_at') THEN
        CREATE TRIGGER trg_files_updated_at
            BEFORE UPDATE ON files
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Create the file_owners table
CREATE TABLE IF NOT EXISTS file_owners (
    developer_id UUID NOT NULL,
    file_id UUID NOT NULL,
    owner_type TEXT NOT NULL,  -- 'user' or 'agent'
    owner_id UUID NOT NULL,
    CONSTRAINT pk_file_owners PRIMARY KEY (developer_id, file_id),
    CONSTRAINT fk_file_owners_file FOREIGN KEY (developer_id, file_id) REFERENCES files (developer_id, file_id),
    CONSTRAINT ct_file_owners_owner_type CHECK (owner_type IN ('user', 'agent'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_file_owners_owner ON file_owners (developer_id, owner_type, owner_id);

-- Create function to validate owner reference
CREATE OR REPLACE FUNCTION validate_file_owner()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.owner_type = 'user' THEN
        IF NOT EXISTS (
            SELECT 1 FROM users
            WHERE developer_id = NEW.developer_id AND user_id = NEW.owner_id
        ) THEN
            RAISE EXCEPTION 'Invalid user reference';
        END IF;
    ELSIF NEW.owner_type = 'agent' THEN
        IF NOT EXISTS (
            SELECT 1 FROM agents
            WHERE developer_id = NEW.developer_id AND agent_id = NEW.owner_id
        ) THEN
            RAISE EXCEPTION 'Invalid agent reference';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for validation
CREATE TRIGGER trg_validate_file_owner
BEFORE INSERT OR UPDATE ON file_owners
FOR EACH ROW
EXECUTE FUNCTION validate_file_owner();

COMMIT;
