BEGIN;

-- Temporarily disable compression
ALTER TABLE transitions SET (timescaledb.compress = false);

-- Add the scope field to the transition_cursor type
ALTER TYPE transition_cursor ADD ATTRIBUTE scope_id UUID;

-- Update all existing rows to set the default scope_id
UPDATE transitions 
SET current_step.scope_id = '00000000-0000-0000-0000-000000000000'::UUID
WHERE (current_step).scope_id IS NULL;

UPDATE transitions 
SET next_step.scope_id = '00000000-0000-0000-0000-000000000000'::UUID
WHERE (next_step).workflow_name IS NOT NULL AND (next_step).scope_id IS NULL;

-- Add a check constraint to ensure scope_id is not null for future inserts/updates
ALTER TABLE transitions
    ADD CONSTRAINT ct_transition_cursor_scope_id_not_null
    CHECK ((current_step).scope_id IS NOT NULL AND 
           (next_step IS NULL OR (next_step).scope_id IS NOT NULL));

-- Re-enable compression
ALTER TABLE transitions SET (timescaledb.compress = true);

COMMIT;
