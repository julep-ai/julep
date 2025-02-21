BEGIN;

-- Drop the check constraint first
ALTER TABLE transitions
    DROP CONSTRAINT ct_transition_cursor_scope_id_not_null;

-- Remove the scope field from the transition_cursor type
ALTER TYPE transition_cursor DROP ATTRIBUTE scope_id;

COMMIT;
