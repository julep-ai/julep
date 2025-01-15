BEGIN;

-- Temporarily remove foreign key to modify its behavior
ALTER TABLE executions
    DROP CONSTRAINT IF EXISTS fk_executions_task;

-- Recreate foreign key with cascading deletes
ALTER TABLE executions
    ADD CONSTRAINT fk_executions_task
    FOREIGN KEY (developer_id, task_id, task_version)
    REFERENCES tasks (developer_id, task_id, "version")
    ON DELETE CASCADE;

COMMIT;
