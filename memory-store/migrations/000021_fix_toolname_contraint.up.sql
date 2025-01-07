BEGIN;

-- Drop the existing unique constraint
ALTER TABLE tools DROP CONSTRAINT IF EXISTS ct_unique_name_per_agent;

-- Add the new unique constraint including developer_id
ALTER TABLE tools ADD CONSTRAINT ct_unique_name_per_agent 
UNIQUE (developer_id, agent_id, name, task_id);

COMMIT;
