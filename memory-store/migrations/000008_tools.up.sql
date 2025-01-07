BEGIN;

-- Create tools table if it doesn't exist
CREATE TABLE IF NOT EXISTS tools (
    developer_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    tool_id UUID NOT NULL,
    task_id UUID DEFAULT NULL,
    type TEXT NOT NULL CONSTRAINT ct_tools_type_length CHECK (
        length(type) >= 1
        AND length(type) <= 255
    ),
    name TEXT NOT NULL CONSTRAINT ct_tools_name_length CHECK (
        length(name) >= 1
        AND length(name) <= 255
    ),
    description TEXT CONSTRAINT ct_tools_description_length CHECK (
        description IS NULL
        OR length(description) <= 1000
    ),
    spec JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_tools PRIMARY KEY (developer_id, agent_id, tool_id),
    CONSTRAINT ct_unique_name_per_agent UNIQUE (agent_id, name, task_id),
    CONSTRAINT ct_spec_is_object CHECK (jsonb_typeof(spec) = 'object')
);

-- Create sorted index on task_id if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_tools_task_id_sorted ON tools (task_id DESC)
WHERE
    task_id IS NOT NULL;

-- Create foreign key constraint and index if they don't exist
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_tools_agent'
    ) THEN
        ALTER TABLE tools
            ADD CONSTRAINT fk_tools_agent
            FOREIGN KEY (developer_id, agent_id)
            REFERENCES agents(developer_id, agent_id) ON DELETE CASCADE;
    END IF;
END $$;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS trg_tools_updated_at ON tools;

CREATE TRIGGER trg_tools_updated_at BEFORE
UPDATE ON tools FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column ();

-- Add comment to table
COMMENT ON TABLE tools IS 'Stores tool configurations and specifications for AI agents';

COMMIT;
