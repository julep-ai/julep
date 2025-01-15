BEGIN;

-- Remove cascading foreign key constraint
ALTER TABLE executions
    DROP CONSTRAINT IF EXISTS fk_executions_task;

-- Restore original foreign key without cascading behavior
ALTER TABLE executions
    ADD CONSTRAINT fk_executions_task
    FOREIGN KEY (developer_id, task_id, task_version)
    REFERENCES tasks (developer_id, task_id, "version");

COMMIT;
