-- Enable the pg_trgm extension if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Add trigram indexes if not already present
-- These indexes already exist in 000006_docs.up.sql, but we'll ensure they're created
CREATE INDEX IF NOT EXISTS idx_docs_title_trgm ON docs USING GIN (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_docs_content_trgm ON docs USING GIN (content gin_trgm_ops);

DROP FUNCTION IF EXISTS search_by_text;

-- Create a new function that combines full-text search with trigram similarity
CREATE OR REPLACE FUNCTION search_by_text (
    developer_id UUID,
    query_text text,
    owner_types TEXT[],
    owner_ids UUID[],
    search_language text DEFAULT 'english_unaccent',
    k integer DEFAULT 3,
    metadata_filter jsonb DEFAULT NULL,
    similarity_threshold float DEFAULT 0.3
) RETURNS SETOF doc_search_result LANGUAGE plpgsql AS $$
DECLARE
    ts_query tsquery;
BEGIN
    IF array_length(owner_types, 1) != array_length(owner_ids, 1) THEN
        RAISE EXCEPTION 'owner_types and owner_ids must be the same length';
    END IF;

    -- Convert query to tsquery
    ts_query := websearch_to_tsquery(search_language::regconfig, query_text);

    RETURN QUERY EXECUTE 
        'WITH tsv_results AS (
            SELECT
                d.developer_id,
                d.doc_id,
                d.index,
                d.title,
                d.content,
                ts_rank_cd(d.search_tsv, $1, 32)::double precision as tsv_score,
                e.embedding,
                d.metadata,
                doc_owners.owner_type,
                doc_owners.owner_id
            FROM docs d
            LEFT JOIN docs_embeddings e
                ON e.developer_id = d.developer_id
                AND e.doc_id = d.doc_id
                AND e.index = d.index
            LEFT JOIN doc_owners ON d.doc_id = doc_owners.doc_id
            WHERE d.developer_id = $2
            AND d.search_tsv @@ $1
            AND (array_length($3, 1) IS NULL OR doc_owners.owner_type = ANY($3))
            AND (array_length($4, 1) IS NULL OR doc_owners.owner_id = ANY($4))
            AND (($5)::jsonb IS NULL OR d.metadata @> ($5)::jsonb)
        ),
        trigram_results AS (
            SELECT
                d.developer_id,
                d.doc_id,
                d.index,
                d.title,
                d.content,
                GREATEST(
                    similarity(d.title, $6),
                    similarity(d.content, $6)
                )::double precision as trigram_score,
                e.embedding,
                d.metadata,
                doc_owners.owner_type,
                doc_owners.owner_id
            FROM docs d
            LEFT JOIN docs_embeddings e
                ON e.developer_id = d.developer_id
                AND e.doc_id = d.doc_id
                AND e.index = d.index
            LEFT JOIN doc_owners ON d.doc_id = doc_owners.doc_id
            WHERE d.developer_id = $2
            AND GREATEST(
                similarity(d.title, $6),
                similarity(d.content, $6)
            ) > $7
            AND (array_length($3, 1) IS NULL OR doc_owners.owner_type = ANY($3))
            AND (array_length($4, 1) IS NULL OR doc_owners.owner_id = ANY($4))
            AND (($5)::jsonb IS NULL OR d.metadata @> ($5)::jsonb)
            AND NOT EXISTS (
                SELECT 1 FROM tsv_results tr 
                WHERE tr.doc_id = d.doc_id AND tr.index = d.index
            )
        ),
        combined_results AS (
            SELECT *, tsv_score as score, 1 as source FROM tsv_results
            UNION ALL
            SELECT *, trigram_score as score, 2 as source FROM trigram_results
        )
        SELECT 
            developer_id,
            doc_id,
            index,
            title,
            content,
            score as distance,
            embedding,
            metadata,
            owner_type,
            owner_id
        FROM combined_results
        ORDER BY score DESC
        LIMIT $8'
    USING
        ts_query,
        developer_id,
        owner_types,
        owner_ids,
        metadata_filter,
        query_text,
        similarity_threshold,
        k;
END;
$$;

DROP FUNCTION IF EXISTS search_hybrid;

-- Update the hybrid search function to use trigram similarity as well
CREATE OR REPLACE FUNCTION search_hybrid (
    developer_id UUID,
    query_text text,
    query_embedding vector (1024),
    owner_types TEXT[],
    owner_ids UUID [],
    k integer DEFAULT 3,
    alpha float DEFAULT 0.7, -- Weight for embedding results
    confidence float DEFAULT 0.5,
    metadata_filter jsonb DEFAULT NULL,
    search_language text DEFAULT 'english_unaccent',
    similarity_threshold float DEFAULT 0.3
) RETURNS SETOF doc_search_result AS $$
DECLARE
    ts_query tsquery;
BEGIN
    IF array_length(owner_types, 1) != array_length(owner_ids, 1) THEN
        RAISE EXCEPTION 'owner_types and owner_ids must be the same length';
    END IF;

    -- Convert query to tsquery
    ts_query := websearch_to_tsquery(search_language::regconfig, query_text);

    RETURN QUERY EXECUTE 
        'WITH vector_results AS (
            SELECT
                d.developer_id,
                d.doc_id,
                d.index,
                d.title,
                d.content,
                1 - (e.embedding <=> $9) as vector_score,
                e.embedding,
                d.metadata,
                doc_owners.owner_type,
                doc_owners.owner_id
            FROM docs d
            JOIN docs_embeddings e
                ON e.developer_id = d.developer_id
                AND e.doc_id = d.doc_id
                AND e.index = d.index
            LEFT JOIN doc_owners ON d.doc_id = doc_owners.doc_id
            WHERE d.developer_id = $1
            AND 1 - (e.embedding <=> $9) > $8
            AND (array_length($2, 1) IS NULL OR doc_owners.owner_type = ANY($2))
            AND (array_length($3, 1) IS NULL OR doc_owners.owner_id = ANY($3))
            AND (($4)::jsonb IS NULL OR d.metadata @> ($4)::jsonb)
        ),
        tsv_results AS (
            SELECT
                d.developer_id,
                d.doc_id,
                d.index,
                d.title,
                d.content,
                ts_rank_cd(d.search_tsv, $5, 32)::double precision as tsv_score,
                e.embedding,
                d.metadata,
                doc_owners.owner_type,
                doc_owners.owner_id
            FROM docs d
            LEFT JOIN docs_embeddings e
                ON e.developer_id = d.developer_id
                AND e.doc_id = d.doc_id
                AND e.index = d.index
            LEFT JOIN doc_owners ON d.doc_id = doc_owners.doc_id
            WHERE d.developer_id = $1
            AND d.search_tsv @@ $5
            AND (array_length($2, 1) IS NULL OR doc_owners.owner_type = ANY($2))
            AND (array_length($3, 1) IS NULL OR doc_owners.owner_id = ANY($3))
            AND (($4)::jsonb IS NULL OR d.metadata @> ($4)::jsonb)
        ),
        trigram_results AS (
            SELECT
                d.developer_id,
                d.doc_id,
                d.index,
                d.title,
                d.content,
                GREATEST(
                    similarity(d.title, $10),
                    similarity(d.content, $10)
                )::double precision as trigram_score,
                e.embedding,
                d.metadata,
                doc_owners.owner_type,
                doc_owners.owner_id
            FROM docs d
            LEFT JOIN docs_embeddings e
                ON e.developer_id = d.developer_id
                AND e.doc_id = d.doc_id
                AND e.index = d.index
            LEFT JOIN doc_owners ON d.doc_id = doc_owners.doc_id
            WHERE d.developer_id = $1
            AND GREATEST(
                similarity(d.title, $10),
                similarity(d.content, $10)
            ) > $11
            AND (array_length($2, 1) IS NULL OR doc_owners.owner_type = ANY($2))
            AND (array_length($3, 1) IS NULL OR doc_owners.owner_id = ANY($3))
            AND (($4)::jsonb IS NULL OR d.metadata @> ($4)::jsonb)
            AND NOT EXISTS (
                SELECT 1 FROM tsv_results tr 
                WHERE tr.doc_id = d.doc_id AND tr.index = d.index
            )
        ),
        text_results AS (
            SELECT *, tsv_score as text_score FROM tsv_results
            UNION ALL
            SELECT *, trigram_score as text_score FROM trigram_results
        ),
        normalized_scores AS (
            SELECT
                COALESCE(v.developer_id, t.developer_id) as developer_id,
                COALESCE(v.doc_id, t.doc_id) as doc_id,
                COALESCE(v.index, t.index) as index,
                COALESCE(v.title, t.title) as title,
                COALESCE(v.content, t.content) as content,
                COALESCE(v.vector_score, 0) as vector_score,
                COALESCE(t.text_score, 0) as text_score,
                COALESCE(v.embedding, t.embedding) as embedding,
                COALESCE(v.metadata, t.metadata) as metadata,
                COALESCE(v.owner_type, t.owner_type) as owner_type,
                COALESCE(v.owner_id, t.owner_id) as owner_id
            FROM vector_results v
            FULL OUTER JOIN text_results t
                ON v.doc_id = t.doc_id
                AND v.index = t.index
        ),
        combined_scores AS (
            SELECT
                developer_id,
                doc_id,
                index,
                title,
                content,
                ($6 * vector_score + (1 - $6) * text_score) as combined_score,
                embedding,
                metadata,
                owner_type,
                owner_id
            FROM normalized_scores
        )
        SELECT
            developer_id,
            doc_id,
            index,
            title,
            content,
            combined_score as distance,
            embedding,
            metadata,
            owner_type,
            owner_id
        FROM combined_scores
        ORDER BY combined_score DESC
        LIMIT $7'
    USING
        developer_id,
        owner_types,
        owner_ids,
        metadata_filter,
        ts_query,
        alpha,
        k,
        confidence,
        query_embedding,
        query_text,
        similarity_threshold;
END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS embed_and_search_hybrid;

-- Update the embed_and_search_hybrid function to use the updated search_hybrid function
CREATE OR REPLACE FUNCTION embed_and_search_hybrid (
    developer_id UUID,
    query_text text,
    owner_types TEXT[],
    owner_ids UUID [],
    k integer DEFAULT 3,
    alpha float DEFAULT 0.7,
    confidence float DEFAULT 0.5,
    metadata_filter jsonb DEFAULT NULL,
    search_language text DEFAULT 'english_unaccent',
    embedding_provider text DEFAULT 'openai',
    embedding_model text DEFAULT 'text-embedding-3-large',
    input_type text DEFAULT 'query',
    api_key text DEFAULT NULL,
    api_key_name text DEFAULT NULL,
    similarity_threshold float DEFAULT 0.3
) RETURNS SETOF doc_search_result AS $$
DECLARE
    query_embedding vector(1024);
BEGIN
    -- Get embedding for the query
    query_embedding := embed_with_cache(
        embedding_provider,
        embedding_model,
        query_text,
        input_type,
        api_key,
        api_key_name
    );

    -- Call the search_hybrid function with the embedding
    RETURN QUERY
    SELECT * FROM search_hybrid(
        developer_id,
        query_text,
        query_embedding,
        owner_types,
        owner_ids,
        k,
        alpha,
        confidence,
        metadata_filter,
        search_language,
        similarity_threshold
    );
END;
$$ LANGUAGE plpgsql; 