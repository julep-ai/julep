BEGIN;

-- Drop triggers first
DROP TRIGGER IF EXISTS trg_validate_participant_before_update ON session_lookup;
DROP TRIGGER IF EXISTS trg_validate_participant_before_insert ON session_lookup;

-- Drop the validation function
DROP FUNCTION IF EXISTS validate_participant();

-- Drop session_lookup table and its indexes
DROP TABLE IF EXISTS session_lookup;

-- Drop sessions table and its indexes
DROP TRIGGER IF EXISTS trg_sessions_updated_at ON sessions;
DROP TABLE IF EXISTS sessions CASCADE;

-- Drop the enum type
DROP TYPE IF EXISTS participant_type;

COMMIT;