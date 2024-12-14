BEGIN;

-- Drop indexes
DROP INDEX IF EXISTS idx_docs_content_trgm;
DROP INDEX IF EXISTS idx_docs_title_trgm;
DROP INDEX IF EXISTS idx_docs_search_tsv;
DROP INDEX IF EXISTS idx_docs_metadata;
DROP INDEX IF EXISTS idx_agent_docs_agent;
DROP INDEX IF EXISTS idx_user_docs_user;
DROP INDEX IF EXISTS idx_docs_developer;
DROP INDEX IF EXISTS idx_docs_id_sorted;

-- Drop triggers
DROP TRIGGER IF EXISTS trg_docs_search_tsv ON docs;
DROP TRIGGER IF EXISTS trg_docs_updated_at ON docs;

-- Drop the constraint that depends on is_valid_language function
ALTER TABLE IF EXISTS docs DROP CONSTRAINT IF EXISTS ct_docs_valid_language;

-- Drop functions
DROP FUNCTION IF EXISTS docs_update_search_tsv();
DROP FUNCTION IF EXISTS is_valid_language(text);

-- Drop tables (in correct order due to foreign key constraints)
DROP TABLE IF EXISTS agent_docs;
DROP TABLE IF EXISTS user_docs;
DROP TABLE IF EXISTS docs;

COMMIT;
