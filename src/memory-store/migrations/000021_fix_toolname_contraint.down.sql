BEGIN;

-- Drop the updated unique constraint
ALTER TABLE tools DROP CONSTRAINT IF EXISTS ct_unique_name_per_agent;

-- Restore the original unique constraint (without developer_id)
ALTER TABLE tools ADD CONSTRAINT ct_unique_name_per_agent 
UNIQUE (agent_id, name, task_id);

COMMIT;