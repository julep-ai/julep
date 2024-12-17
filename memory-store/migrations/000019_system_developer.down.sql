BEGIN;

-- Remove the system developer
DELETE FROM developers 
WHERE developer_id = '00000000-0000-0000-0000-000000000000'::uuid;

COMMIT;
