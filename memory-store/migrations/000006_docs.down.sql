BEGIN;

-- Drop doc_owners table and its dependencies
DROP TRIGGER IF EXISTS trg_validate_doc_owner ON doc_owners;
DROP FUNCTION IF EXISTS validate_doc_owner();
DROP INDEX IF EXISTS idx_doc_owners_owner;
ALTER TABLE IF EXISTS doc_owners DROP CONSTRAINT IF EXISTS fk_doc_owners_doc;
DROP TABLE IF EXISTS doc_owners CASCADE;

-- Drop docs table and its dependencies
DROP TRIGGER IF EXISTS trg_docs_search_tsv ON docs;
DROP TRIGGER IF EXISTS trg_docs_updated_at ON docs;
DROP FUNCTION IF EXISTS docs_update_search_tsv();

-- Drop indexes
DROP INDEX IF EXISTS idx_docs_content_trgm;
DROP INDEX IF EXISTS idx_docs_title_trgm;
DROP INDEX IF EXISTS idx_docs_search_tsv;
DROP INDEX IF EXISTS idx_docs_metadata;
ALTER TABLE IF EXISTS docs DROP CONSTRAINT IF EXISTS uq_docs_developer_doc;

-- Drop docs table
DROP TABLE IF EXISTS docs CASCADE;

-- Drop language validation function
DROP FUNCTION IF EXISTS is_valid_language(text);

COMMIT;
