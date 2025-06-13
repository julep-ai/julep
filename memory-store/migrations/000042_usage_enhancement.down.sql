-- AIDEV-NOTE: 1472:: Rollback migration to remove usage enhancement columns
-- This migration removes the reference fields and provider column added in the up migration

BEGIN;

-- Drop indexes first
DROP INDEX IF EXISTS idx_usage_session_created;
DROP INDEX IF EXISTS idx_usage_execution_created;
DROP INDEX IF EXISTS idx_usage_provider;

-- AIDEV-NOTE: 1472:: No foreign key constraints to drop (hypertables can't have FK constraints to other hypertables)

-- Drop columns
ALTER TABLE usage
    DROP COLUMN IF EXISTS session_id,
    DROP COLUMN IF EXISTS execution_id,
    DROP COLUMN IF EXISTS transition_id,
    DROP COLUMN IF EXISTS entry_id,
    DROP COLUMN IF EXISTS provider;

COMMIT;