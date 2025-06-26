BEGIN;

-- Drop the duplicate doc owner check trigger
DROP TRIGGER IF EXISTS trg_check_duplicate_doc_owner ON doc_owners;

-- Drop the trigger function
DROP FUNCTION IF EXISTS check_duplicate_doc_owner();

-- Drop the content hash trigger
DROP TRIGGER IF EXISTS trg_docs_content_hash ON docs;

-- Drop the content hash function
DROP FUNCTION IF EXISTS docs_update_content_hash();

-- Drop the hash generation function
DROP FUNCTION IF EXISTS generate_content_hash(TEXT, TEXT);

-- Drop the index
DROP INDEX IF EXISTS idx_docs_content_hash;

-- Remove the content_hash column
ALTER TABLE docs DROP COLUMN IF EXISTS content_hash;

COMMIT; 