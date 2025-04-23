-- Reset work_mem to default (or a reasonable value)
RESET work_mem;

-- Drop function created in the up migration
DROP FUNCTION IF EXISTS search_by_text;

-- Drop indexes created in the up migration
DROP INDEX IF EXISTS idx_doc_owners_agent_lookup;
DROP INDEX IF EXISTS idx_doc_owners_lookup;

-- Reset statistics
ALTER TABLE docs ALTER COLUMN title SET STATISTICS 100;
ALTER TABLE docs ALTER COLUMN content SET STATISTICS 100;

-- Reset index settings
ALTER INDEX idx_docs_metadata SET (fastupdate=on);
ALTER INDEX search_tsv SET (fastupdate=on);
ALTER INDEX title_trgm SET (fastupdate=on);
ALTER INDEX content_trgm SET (fastupdate=on);

-- Drop the vectorizer with all related data
SELECT ai.drop_vectorizer(id, drop_all => TRUE) FROM ai.vectorizer;

-- Remove hypertable configuration
SELECT remove_hypertable('docs', if_exists => TRUE);

-- Save existing data before making schema changes
CREATE TEMP TABLE docs_temp AS
SELECT * FROM docs;

-- Delete data to allow constraint changes
DELETE FROM docs;

-- First drop the dependent foreign key
ALTER TABLE docs_embeddings_store DROP CONSTRAINT IF EXISTS docs_embeddings_store_developer_id_doc_id_index_fkey;

-- Drop new constraints and restore original primary key
ALTER TABLE docs 
    DROP CONSTRAINT IF EXISTS pk_docs,
    DROP CONSTRAINT IF EXISTS uq_doc_index;

-- Re-add original constraints
ALTER TABLE docs ADD CONSTRAINT pk_docs PRIMARY KEY (developer_id, doc_id);
ALTER TABLE docs ADD CONSTRAINT uq_docs_dev_doc_idx UNIQUE (developer_id, doc_id, index);

-- Restore data
INSERT INTO docs SELECT * FROM docs_temp;
DROP TABLE docs_temp;

-- Recreate the original foreign key if it existed
ALTER TABLE docs_embeddings_store 
    ADD CONSTRAINT docs_embeddings_store_developer_id_doc_id_index_fkey 
    FOREIGN KEY (developer_id, doc_id, index) 
    REFERENCES docs(developer_id, doc_id, index);
