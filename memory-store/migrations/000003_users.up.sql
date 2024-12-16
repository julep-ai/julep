BEGIN;

-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS users (
    developer_id UUID NOT NULL,
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    about TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT pk_users PRIMARY KEY (developer_id, user_id)
);

-- Create sorted index on user_id if it doesn't exist
CREATE INDEX IF NOT EXISTS users_id_sorted_idx ON users (user_id DESC);

-- Create foreign key constraint and index if they don't exist
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'users_developer_id_fkey'
    ) THEN
        ALTER TABLE users 
            ADD CONSTRAINT users_developer_id_fkey 
            FOREIGN KEY (developer_id) 
            REFERENCES developers(developer_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS users_developer_id_idx ON users (developer_id);

-- Create a GIN index on the entire metadata column if it doesn't exist
CREATE INDEX IF NOT EXISTS users_metadata_gin_idx ON users USING GIN (metadata);

-- Create trigger if it doesn't exist
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_users_updated_at'
    ) THEN
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Add comment to table (comments are idempotent by default)
COMMENT ON TABLE users IS 'Stores user information linked to developers';

COMMIT;