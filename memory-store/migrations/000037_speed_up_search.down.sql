BEGIN;
-- Reset work_mem to default (or a reasonable value)
RESET work_mem;

-- Drop indexes created in the up migration
DROP INDEX IF EXISTS idx_doc_owners_agent_lookup;
DROP INDEX IF EXISTS idx_doc_owners_lookup;

-- Reset statistics
ALTER TABLE docs ALTER COLUMN title SET STATISTICS 100;
ALTER TABLE docs ALTER COLUMN content SET STATISTICS 100;

-- Reset index settings
ALTER INDEX idx_docs_metadata SET (fastupdate=on);
ALTER INDEX idx_docs_search_tsv SET (fastupdate=on);
ALTER INDEX idx_docs_title_trgm SET (fastupdate=on);
ALTER INDEX idx_docs_content_trgm SET (fastupdate=on);

END;