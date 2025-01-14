BEGIN;

-- Drop the updated constraints
ALTER TABLE agents
DROP CONSTRAINT IF EXISTS ct_agents_about_length;

ALTER TABLE tools
DROP CONSTRAINT IF EXISTS ct_tools_description_length;

ALTER TABLE files
DROP CONSTRAINT IF EXISTS ct_files_description_length;

ALTER TABLE tasks
DROP CONSTRAINT IF EXISTS ct_tasks_description_length;

-- Restore original constraints
ALTER TABLE tools
ADD CONSTRAINT ct_tools_description_length CHECK (
    description IS NULL
    OR length(description) <= 1000
);

ALTER TABLE files
ADD CONSTRAINT ct_files_description_length CHECK (
    description IS NULL
    OR length(description) <= 1000
);

ALTER TABLE tasks
ADD CONSTRAINT ct_tasks_description_length CHECK (
    description IS NULL
    OR length(description) <= 1000
);

COMMIT;