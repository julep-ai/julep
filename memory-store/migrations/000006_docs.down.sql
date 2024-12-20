BEGIN;

-- Drop doc_owners table and its dependencies
DROP TRIGGER IF EXISTS trg_validate_doc_owner ON doc_owners;
DROP FUNCTION IF EXISTS validate_doc_owner();
DROP TABLE IF EXISTS doc_owners;

-- Drop docs table and its dependencies
DROP TRIGGER IF EXISTS trg_docs_search_tsv ON docs;
DROP TRIGGER IF EXISTS trg_docs_updated_at ON docs;
DROP FUNCTION IF EXISTS docs_update_search_tsv();

-- Drop indexes
DROP INDEX IF EXISTS idx_docs_content_trgm;
DROP INDEX IF EXISTS idx_docs_title_trgm;
DROP INDEX IF EXISTS idx_docs_search_tsv;
DROP INDEX IF EXISTS idx_docs_metadata;
DROP INDEX IF EXISTS idx_docs_developer;
DROP INDEX IF EXISTS idx_docs_id_sorted;

-- Drop docs table
DROP TABLE IF EXISTS docs;

-- Drop language validation function
DROP FUNCTION IF EXISTS is_valid_language(text);

COMMIT;
