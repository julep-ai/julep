BEGIN;

-- Add the scope field to the transition_cursor type
ALTER TYPE transition_cursor ADD ATTRIBUTE scope_id UUID;

COMMIT;
