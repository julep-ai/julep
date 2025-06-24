-- AIDEV-NOTE: 1472:: Migration to add reference fields and provider to usage table
-- This migration adds context fields to track which session/execution/transition/entry
-- generated the usage, along with the actual provider used

BEGIN;

-- Add new columns to usage table
ALTER TABLE usage
    ADD COLUMN session_id UUID NULL,
    ADD COLUMN execution_id UUID NULL,
    ADD COLUMN transition_id UUID NULL,
    ADD COLUMN entry_id UUID NULL,
    ADD COLUMN provider TEXT NULL;

-- AIDEV-NOTE: 1472:: TimescaleDB hypertables cannot have foreign key constraints to other hypertables
-- We rely on application-level referential integrity for these fields

-- Create indexes for efficient querying
CREATE INDEX idx_usage_session_created
    ON usage(developer_id, session_id, created_at DESC)
    WHERE session_id IS NOT NULL;

CREATE INDEX idx_usage_execution_created
    ON usage(developer_id, execution_id, created_at DESC)
    WHERE execution_id IS NOT NULL;

CREATE INDEX idx_usage_provider
    ON usage(provider)
    WHERE provider IS NOT NULL;

-- Add comment to explain the purpose of new fields
COMMENT ON COLUMN usage.session_id IS 'Reference to the session that generated this usage';
COMMENT ON COLUMN usage.execution_id IS 'Reference to the task execution that generated this usage';
COMMENT ON COLUMN usage.transition_id IS 'Reference to the specific transition step that generated this usage';
COMMENT ON COLUMN usage.entry_id IS 'Reference to the chat entry that generated this usage';
COMMENT ON COLUMN usage.provider IS 'The actual LLM provider used (e.g., openai, anthropic, google)';

COMMIT;