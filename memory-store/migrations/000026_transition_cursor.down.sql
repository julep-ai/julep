BEGIN;

-- Remove the scope field from the transition_cursor type
ALTER TYPE transition_cursor DROP ATTRIBUTE scope_id;

COMMIT;
