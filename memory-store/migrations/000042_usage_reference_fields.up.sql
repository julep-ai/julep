BEGIN;

-- Add reference columns to usage table
ALTER TABLE usage
    ADD COLUMN execution_id UUID,
    ADD COLUMN transition_id UUID,
    ADD COLUMN session_id UUID,
    ADD COLUMN entry_id UUID,
    ADD COLUMN provider TEXT;

-- Index new columns for query efficiency
CREATE INDEX IF NOT EXISTS idx_usage_execution_id ON usage (execution_id);
CREATE INDEX IF NOT EXISTS idx_usage_transition_id ON usage (transition_id);
CREATE INDEX IF NOT EXISTS idx_usage_session_id ON usage (session_id);
CREATE INDEX IF NOT EXISTS idx_usage_entry_id ON usage (entry_id);
CREATE INDEX IF NOT EXISTS idx_usage_provider ON usage (provider);

COMMENT ON COLUMN usage.provider IS 'Model provider for monitoring';

COMMIT;
