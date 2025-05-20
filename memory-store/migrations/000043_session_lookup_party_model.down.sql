-- Revert session_lookup to participant-based model
ALTER TABLE session_lookup DROP CONSTRAINT IF EXISTS fk_session_lookup_party;
ALTER TABLE session_lookup DROP CONSTRAINT IF EXISTS session_lookup_pkey;

-- Recreate participant_type enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'participant_type') THEN
        CREATE TYPE participant_type AS ENUM ('user', 'agent');
    END IF;
END $$;

ALTER TABLE session_lookup ADD COLUMN IF NOT EXISTS participant_type participant_type;
ALTER TABLE session_lookup ADD COLUMN IF NOT EXISTS participant_id UUID;

UPDATE session_lookup sl
SET participant_type = p.party_type,
    participant_id = p.party_id
FROM parties p
WHERE sl.party_id = p.party_id
  AND sl.developer_id = p.developer_id;

ALTER TABLE session_lookup ALTER COLUMN participant_type SET NOT NULL;
ALTER TABLE session_lookup ALTER COLUMN participant_id SET NOT NULL;
ALTER TABLE session_lookup ADD PRIMARY KEY (developer_id, session_id, participant_type, participant_id);
DROP INDEX IF EXISTS idx_session_lookup_by_party;
CREATE INDEX IF NOT EXISTS idx_session_lookup_by_participant ON session_lookup (developer_id, participant_type, participant_id);
ALTER TABLE session_lookup DROP COLUMN IF EXISTS party_id;

-- Recreate legacy owner tables
CREATE TABLE IF NOT EXISTS doc_owners (
    developer_id UUID NOT NULL,
    doc_id UUID NOT NULL,
    owner_type TEXT NOT NULL,
    owner_id UUID NOT NULL,
    PRIMARY KEY (developer_id, doc_id)
);
INSERT INTO doc_owners (developer_id, doc_id, owner_type, owner_id)
SELECT d.developer_id, d.doc_id, p.party_type, p.party_id
FROM document_owners d
JOIN parties p ON d.developer_id = p.developer_id AND d.party_id = p.party_id;

CREATE TABLE IF NOT EXISTS file_owners (
    developer_id UUID NOT NULL,
    file_id UUID NOT NULL,
    owner_type TEXT NOT NULL,
    owner_id UUID NOT NULL,
    PRIMARY KEY (developer_id, file_id)
);
ALTER TABLE file_owners_party RENAME TO file_owners_tmp;
INSERT INTO file_owners (developer_id, file_id, owner_type, owner_id)
SELECT f.developer_id, f.file_id, p.party_type, p.party_id
FROM file_owners_tmp f
JOIN parties p ON f.developer_id = p.developer_id AND f.party_id = p.party_id;
DROP TABLE file_owners_tmp;
