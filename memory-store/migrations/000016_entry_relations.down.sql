BEGIN;

-- Drop trigger first
DROP TRIGGER IF EXISTS trg_enforce_leaf_nodes ON entry_relations;

-- Drop function
DROP FUNCTION IF EXISTS enforce_leaf_nodes ();

-- Drop the table and its constraints
DROP TABLE IF EXISTS entry_relations CASCADE;

COMMIT;