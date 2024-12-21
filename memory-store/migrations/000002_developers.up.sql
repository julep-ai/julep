BEGIN;

-- Create developers table
CREATE TABLE IF NOT EXISTS developers (
    developer_id UUID NOT NULL,
    email TEXT NOT NULL CONSTRAINT ct_developers_email_format CHECK (
        email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    ),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    settings JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_developers PRIMARY KEY (developer_id),
    CONSTRAINT uq_developers_email UNIQUE (email)
);

-- Create index on email
CREATE INDEX IF NOT EXISTS idx_developers_email ON developers (email);

-- Create GIN index for tags array
CREATE INDEX IF NOT EXISTS idx_developers_tags ON developers USING GIN (tags);

-- Create partial index for active developers
CREATE INDEX IF NOT EXISTS idx_developers_active ON developers (developer_id)
WHERE
    active = TRUE;

-- Create trigger to automatically update updated_at
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_developers_updated_at') THEN
        CREATE TRIGGER trg_developers_updated_at
            BEFORE UPDATE ON developers
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;

-- Add comment to table
COMMENT ON TABLE developers IS 'Stores developer information including their settings and tags';

COMMIT;
