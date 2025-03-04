BEGIN;

-- First remove the new column and its constraint from agents table
ALTER TABLE agents 
DROP CONSTRAINT ct_agents_default_system_template_not_empty;

ALTER TABLE agents 
DROP COLUMN default_system_template;

-- Then restore the original constraint on sessions table
ALTER TABLE sessions 
DROP CONSTRAINT ct_sessions_system_template_not_empty;

ALTER TABLE sessions 
ADD CONSTRAINT ct_sessions_system_template_not_empty CHECK (
    length(trim(system_template)) > 0
);

COMMIT; 