-- Create developers table
CREATE TABLE developers (
    developer_id UUID NOT NULL,
    email TEXT NOT NULL CONSTRAINT ct_developers_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    active BOOLEAN NOT NULL DEFAULT true,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    settings JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_developers PRIMARY KEY (developer_id),
    CONSTRAINT uq_developers_email UNIQUE (email)
);

-- Create sorted index on developer_id (optimized for UUID v7)
CREATE INDEX idx_developers_id_sorted ON developers (developer_id DESC);

-- Create index on email
CREATE INDEX idx_developers_email ON developers (email);

-- Create GIN index for tags array
CREATE INDEX idx_developers_tags ON developers USING GIN (tags);

-- Create partial index for active developers
CREATE INDEX idx_developers_active ON developers (developer_id) WHERE active = true;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trg_developers_updated_at
    BEFORE UPDATE ON developers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment to table
COMMENT ON TABLE developers IS 'Stores developer information including their settings and tags';