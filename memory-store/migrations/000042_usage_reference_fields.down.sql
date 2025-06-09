BEGIN;

-- Remove reference columns from usage table
ALTER TABLE usage
    DROP COLUMN IF EXISTS execution_id,
    DROP COLUMN IF EXISTS transition_id,
    DROP COLUMN IF EXISTS session_id,
    DROP COLUMN IF EXISTS entry_id,
    DROP COLUMN IF EXISTS provider;

DROP INDEX IF EXISTS idx_usage_execution_id;
DROP INDEX IF EXISTS idx_usage_transition_id;
DROP INDEX IF EXISTS idx_usage_session_id;
DROP INDEX IF EXISTS idx_usage_entry_id;
DROP INDEX IF EXISTS idx_usage_provider;

COMMIT;
