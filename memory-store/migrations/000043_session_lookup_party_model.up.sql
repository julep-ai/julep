-- AIDEV-NOTE: Normalize session_lookup to use parties
-- Add party_id column
ALTER TABLE session_lookup ADD COLUMN IF NOT EXISTS party_id UUID;

-- Populate party_id from existing participant columns
UPDATE session_lookup sl
SET party_id = u.party_id
FROM users u
WHERE sl.participant_type = 'user'
  AND sl.developer_id = u.developer_id
  AND sl.participant_id = u.user_id;

UPDATE session_lookup sl
SET party_id = a.party_id
FROM agents a
WHERE sl.participant_type = 'agent'
  AND sl.developer_id = a.developer_id
  AND sl.participant_id = a.agent_id;

-- Enforce not null and add foreign key
ALTER TABLE session_lookup ALTER COLUMN party_id SET NOT NULL;
ALTER TABLE session_lookup
    ADD CONSTRAINT fk_session_lookup_party FOREIGN KEY (developer_id, party_id)
        REFERENCES parties (developer_id, party_id) ON DELETE CASCADE;

-- Update primary key and indexes
ALTER TABLE session_lookup DROP CONSTRAINT IF EXISTS session_lookup_pkey;
ALTER TABLE session_lookup ADD PRIMARY KEY (developer_id, session_id, party_id);
DROP INDEX IF EXISTS idx_session_lookup_by_participant;
CREATE INDEX IF NOT EXISTS idx_session_lookup_by_party ON session_lookup (developer_id, party_id);

-- Remove old validation triggers and columns
DROP TRIGGER IF EXISTS trg_validate_participant_before_insert ON session_lookup;
DROP TRIGGER IF EXISTS trg_validate_participant_before_update ON session_lookup;
DROP FUNCTION IF EXISTS validate_participant();
ALTER TABLE session_lookup DROP COLUMN IF EXISTS participant_type;
ALTER TABLE session_lookup DROP COLUMN IF EXISTS participant_id;
DROP TYPE IF EXISTS participant_type;

-- Drop legacy owner tables and rename new ones
DROP TRIGGER IF EXISTS trg_validate_doc_owner ON doc_owners;
DROP FUNCTION IF EXISTS validate_doc_owner();
DROP TABLE IF EXISTS doc_owners CASCADE;

DROP TRIGGER IF EXISTS trg_validate_file_owner ON file_owners;
DROP FUNCTION IF EXISTS validate_file_owner();
DROP TABLE IF EXISTS file_owners;
ALTER TABLE IF EXISTS file_owners_party RENAME TO file_owners;
