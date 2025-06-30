BEGIN;

-- Drop trigger first
DROP TRIGGER IF EXISTS trg_agents_updated_at ON agents;

-- Drop indexes
DROP INDEX IF EXISTS idx_agents_metadata;

-- Drop table (this will automatically drop associated constraints)
DROP TABLE IF EXISTS agents CASCADE;

COMMIT;
