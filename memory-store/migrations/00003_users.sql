-- Create users table
CREATE TABLE users (
    developer_id UUID NOT NULL,
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    about TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT pk_users PRIMARY KEY (developer_id, user_id)
);

-- Create sorted index on user_id (optimized for UUID v7)
CREATE INDEX users_id_sorted_idx ON users (user_id DESC);

-- Create foreign key constraint and index on developer_id
ALTER TABLE users 
    ADD CONSTRAINT users_developer_id_fkey 
    FOREIGN KEY (developer_id) 
    REFERENCES developers(developer_id);

CREATE INDEX users_developer_id_idx ON users (developer_id);

-- Create a GIN index on the entire metadata column
CREATE INDEX users_metadata_gin_idx ON users USING GIN (metadata);

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment to table
COMMENT ON TABLE users IS 'Stores user information linked to developers';