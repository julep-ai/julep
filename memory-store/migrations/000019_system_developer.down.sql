BEGIN;

-- Remove the system developer
DELETE FROM docs
WHERE developer_id = '00000000-0000-0000-0000-000000000000'::uuid;

-- Remove the system developer
DELETE FROM executions
WHERE developer_id = '00000000-0000-0000-0000-000000000000'::uuid;

-- Remove the system developer
DELETE FROM tasks
WHERE developer_id = '00000000-0000-0000-0000-000000000000'::uuid;

-- Remove the system developer
DELETE FROM agents
WHERE developer_id = '00000000-0000-0000-0000-000000000000'::uuid;

-- Remove the system developer
DELETE FROM users
WHERE developer_id = '00000000-0000-0000-0000-000000000000'::uuid;

-- Remove the system developer
DELETE FROM "sessions"
WHERE developer_id = '00000000-0000-0000-0000-000000000000'::uuid;

-- Remove the system developer
DELETE FROM developers
WHERE developer_id = '00000000-0000-0000-0000-000000000000'::uuid;

COMMIT;
