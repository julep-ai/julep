-- Drop new tables and constraints introduced in the party model migration
DROP TABLE IF EXISTS file_owners_party;
DROP TABLE IF EXISTS document_owners;
ALTER TABLE agents DROP CONSTRAINT IF EXISTS uq_agents_party;
ALTER TABLE agents DROP CONSTRAINT IF EXISTS fk_agents_party;
ALTER TABLE agents DROP COLUMN IF EXISTS party_id;
ALTER TABLE users DROP CONSTRAINT IF EXISTS uq_users_party;
ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_party;
ALTER TABLE users DROP COLUMN IF EXISTS party_id;
DROP TABLE IF EXISTS parties;
