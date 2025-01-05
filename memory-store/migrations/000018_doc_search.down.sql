BEGIN;

-- Drop the embed and search hybrid function
DROP FUNCTION IF EXISTS embed_and_search_hybrid;

-- Drop the hybrid search function
DROP FUNCTION IF EXISTS search_hybrid;

-- Drop the text search function
DROP FUNCTION IF EXISTS search_by_text;

-- Drop the combined embed and search function
DROP FUNCTION IF EXISTS embed_and_search_by_vector;

-- Drop the search function
DROP FUNCTION IF EXISTS search_by_vector;

-- Drop the doc_search_result type
DROP TYPE IF EXISTS doc_search_result;

-- Drop the embed_with_cache function
DROP FUNCTION IF EXISTS embed_with_cache;

-- Drop the embeddings cache table
DROP TABLE IF EXISTS embeddings_cache CASCADE;

COMMIT;
