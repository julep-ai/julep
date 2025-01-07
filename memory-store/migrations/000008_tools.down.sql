BEGIN;

-- Drop table and all its dependent objects (indexes, constraints, triggers)
DROP TABLE IF EXISTS tools CASCADE;

COMMIT;
