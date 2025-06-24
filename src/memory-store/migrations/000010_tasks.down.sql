BEGIN;

-- Drop the foreign key constraint from tools table if it exists
DO $$ 
BEGIN
    IF EXISTS (
        SELECT
            1
        FROM
            information_schema.table_constraints
        WHERE
            constraint_name = 'fk_tools_task_id'
    ) THEN
    ALTER TABLE tools
    DROP CONSTRAINT fk_tools_task_id;

    END IF;
END $$;

-- Drop the workflows table first since it depends on tasks
DROP TABLE IF EXISTS workflows CASCADE;

-- Drop the tasks table and all its dependent objects (CASCADE will handle indexes, triggers, and constraints)
DROP TABLE IF EXISTS tasks CASCADE;

COMMIT;