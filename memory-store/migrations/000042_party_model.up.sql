-- AIDEV-NOTE: Introduces party model for normalized ownership
-- Create parties table
CREATE TABLE IF NOT EXISTS parties (
    developer_id UUID NOT NULL,
    party_id UUID NOT NULL,
    party_type TEXT NOT NULL CHECK (party_type IN ('user','agent')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (developer_id, party_id)
);

-- Backfill parties for existing users
INSERT INTO parties (developer_id, party_id, party_type)
SELECT developer_id, user_id, 'user' FROM users
ON CONFLICT DO NOTHING;

-- Backfill parties for existing agents
INSERT INTO parties (developer_id, party_id, party_type)
SELECT developer_id, agent_id, 'agent' FROM agents
ON CONFLICT DO NOTHING;

-- Add party_id to users
ALTER TABLE users ADD COLUMN IF NOT EXISTS party_id UUID;
UPDATE users SET party_id = user_id WHERE party_id IS NULL;
ALTER TABLE users ALTER COLUMN party_id SET NOT NULL;
ALTER TABLE users
    ADD CONSTRAINT fk_users_party FOREIGN KEY (developer_id, party_id)
        REFERENCES parties (developer_id, party_id),
    ADD CONSTRAINT uq_users_party UNIQUE (party_id);

-- Add party_id to agents
ALTER TABLE agents ADD COLUMN IF NOT EXISTS party_id UUID;
UPDATE agents SET party_id = agent_id WHERE party_id IS NULL;
ALTER TABLE agents ALTER COLUMN party_id SET NOT NULL;
ALTER TABLE agents
    ADD CONSTRAINT fk_agents_party FOREIGN KEY (developer_id, party_id)
        REFERENCES parties (developer_id, party_id),
    ADD CONSTRAINT uq_agents_party UNIQUE (party_id);

-- Create document_owners table referencing parties
CREATE TABLE IF NOT EXISTS document_owners (
    developer_id UUID NOT NULL,
    doc_id UUID NOT NULL,
    party_id UUID NOT NULL,
    PRIMARY KEY (developer_id, doc_id, party_id),
    FOREIGN KEY (developer_id, doc_id) REFERENCES docs (developer_id, doc_id),
    FOREIGN KEY (developer_id, party_id) REFERENCES parties (developer_id, party_id)
);

-- Migrate existing doc owners
INSERT INTO document_owners (developer_id, doc_id, party_id)
SELECT o.developer_id, o.doc_id, o.owner_id
FROM doc_owners o;

-- Create file_owners_party table referencing parties
CREATE TABLE IF NOT EXISTS file_owners_party (
    developer_id UUID NOT NULL,
    file_id UUID NOT NULL,
    party_id UUID NOT NULL,
    PRIMARY KEY (developer_id, file_id, party_id),
    FOREIGN KEY (developer_id, file_id) REFERENCES files (developer_id, file_id),
    FOREIGN KEY (developer_id, party_id) REFERENCES parties (developer_id, party_id)
);

-- Migrate existing file owners
INSERT INTO file_owners_party (developer_id, file_id, party_id)
SELECT o.developer_id, o.file_id, o.owner_id
FROM file_owners o;
