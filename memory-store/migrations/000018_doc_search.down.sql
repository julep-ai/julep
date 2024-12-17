BEGIN;

-- Drop the embed_with_cache function
DROP FUNCTION IF EXISTS embed_with_cache;

-- Drop the embeddings cache table
DROP TABLE IF EXISTS embeddings_cache CASCADE;

COMMIT;
