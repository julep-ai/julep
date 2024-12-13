-- Create files table
CREATE TABLE files (
    developer_id UUID NOT NULL,
    file_id UUID NOT NULL,
    name TEXT NOT NULL CONSTRAINT ct_files_name_length CHECK (length(name) >= 1 AND length(name) <= 255),
    description TEXT DEFAULT NULL CONSTRAINT ct_files_description_length CHECK (description IS NULL OR length(description) <= 1000),
    mime_type TEXT DEFAULT NULL CONSTRAINT ct_files_mime_type_length CHECK (mime_type IS NULL OR length(mime_type) <= 127),
    size BIGINT NOT NULL CONSTRAINT ct_files_size_positive CHECK (size > 0),
    hash BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_files PRIMARY KEY (developer_id, file_id)
);

-- Create sorted index on file_id (optimized for UUID v7)
CREATE INDEX idx_files_id_sorted ON files (file_id DESC);

-- Create foreign key constraint and index on developer_id
ALTER TABLE files 
    ADD CONSTRAINT fk_files_developer 
    FOREIGN KEY (developer_id) 
    REFERENCES developers(developer_id);

CREATE INDEX idx_files_developer ON files (developer_id);

-- Before creating the user_files and agent_files tables, we need to ensure that the file_id is unique for each developer
ALTER TABLE files
    ADD CONSTRAINT uq_files_developer_id_file_id UNIQUE (developer_id, file_id);

-- Create trigger to automatically update updated_at
CREATE TRIGGER trg_files_updated_at
    BEFORE UPDATE ON files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment to table
COMMENT ON TABLE files IS 'Stores file metadata and references for developers';

-- Create the user_files table
CREATE TABLE user_files (
    developer_id UUID NOT NULL,
    user_id UUID NOT NULL,
    file_id UUID NOT NULL,
    CONSTRAINT pk_user_files PRIMARY KEY (developer_id, user_id, file_id),
    CONSTRAINT fk_user_files_user FOREIGN KEY (developer_id, user_id) REFERENCES users(developer_id, user_id),
    CONSTRAINT fk_user_files_file FOREIGN KEY (developer_id, file_id) REFERENCES files(developer_id, file_id)
);

-- Indexes for efficient querying
CREATE INDEX idx_user_files_user ON user_files (developer_id, user_id);

-- Create the agent_files table
CREATE TABLE agent_files (
    developer_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    file_id UUID NOT NULL,
    CONSTRAINT pk_agent_files PRIMARY KEY (developer_id, agent_id, file_id),
    CONSTRAINT fk_agent_files_agent FOREIGN KEY (developer_id, agent_id) REFERENCES agents(developer_id, agent_id),
    CONSTRAINT fk_agent_files_file FOREIGN KEY (developer_id, file_id) REFERENCES files(developer_id, file_id)
);

-- Indexes for efficient querying
CREATE INDEX idx_agent_files_agent ON agent_files (developer_id, agent_id);
