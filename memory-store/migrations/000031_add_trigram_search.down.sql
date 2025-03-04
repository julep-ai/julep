DROP FUNCTION IF EXISTS embed_and_search_hybrid;

-- Revert the embed_and_search_hybrid function to its original form
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
    api_key_name text DEFAULT NULL
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
        search_language
    );
END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS search_hybrid;

-- Revert the search_hybrid function to its original form
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
    search_language text DEFAULT 'english_unaccent'
) RETURNS SETOF doc_search_result AS $$
DECLARE
    owner_filter_sql text := '';
    metadata_filter_sql text := '';
    ts_query tsquery;
BEGIN
    IF array_length(owner_types, 1) != array_length(owner_ids, 1) THEN
        RAISE EXCEPTION 'owner_types and owner_ids must be the same length';
    END IF;

    IF array_length(owner_types, 1) > 0 THEN
        owner_filter_sql := 'AND (doc_owners.owner_type = ANY($3) AND doc_owners.owner_id = ANY($4))';
    END IF;

    IF metadata_filter IS NOT NULL AND jsonb_typeof(metadata_filter) = 'object' AND jsonb_array_length(metadata_filter) > 0 THEN
        metadata_filter_sql := 'AND d.metadata @> $5';
    END IF;

    -- Convert query to tsquery
    ts_query := websearch_to_tsquery(search_language::regconfig, query_text);

    RETURN QUERY EXECUTE format(
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
            WHERE d.developer_id = $6
            AND 1 - (e.embedding <=> $9) > $8
            AND (array_length($3, 1) IS NULL OR (doc_owners.owner_type = ANY($3) AND doc_owners.owner_id = ANY($4)))
            AND (($5)::jsonb IS NULL OR d.metadata @> ($5)::jsonb)
        ),
        tsv_results AS (
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
            WHERE d.developer_id = $6
            AND d.search_tsv @@ $1
            AND (array_length($3, 1) IS NULL OR (doc_owners.owner_type = ANY($3) AND doc_owners.owner_id = ANY($4)))
            AND (($5)::jsonb IS NULL OR d.metadata @> ($5)::jsonb)
        ),
        normalized_scores AS (
            SELECT
                COALESCE(v.developer_id, t.developer_id) as developer_id,
                COALESCE(v.doc_id, t.doc_id) as doc_id,
                COALESCE(v.index, t.index) as index,
                COALESCE(v.title, t.title) as title,
                COALESCE(v.content, t.content) as content,
                COALESCE(v.vector_score, 0) as vector_score,
                COALESCE(t.tsv_score, 0) as tsv_score,
                COALESCE(v.embedding, t.embedding) as embedding,
                COALESCE(v.metadata, t.metadata) as metadata,
                COALESCE(v.owner_type, t.owner_type) as owner_type,
                COALESCE(v.owner_id, t.owner_id) as owner_id
            FROM vector_results v
            FULL OUTER JOIN tsv_results t
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
                ($7 * vector_score + (1 - $7) * tsv_score) as combined_score,
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
        LIMIT $2',
        owner_filter_sql,
        metadata_filter_sql,
        owner_filter_sql,
        metadata_filter_sql
    )
    USING
        ts_query,
        k,
        owner_types,
        owner_ids,
        metadata_filter,
        developer_id,
        alpha,
        confidence,
        query_embedding;
END;
$$ LANGUAGE plpgsql;

-- Note: We don't drop the pg_trgm extension or the trigram indexes
-- as they might be used by other parts of the application 