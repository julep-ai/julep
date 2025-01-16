BEGIN;

-- Hybrid search function combining text and vector search
CREATE
OR REPLACE FUNCTION search_hybrid (
    developer_id UUID,
    query_text text,
    query_embedding vector (1024),
    owner_types TEXT[],
    owner_ids UUID [],
    k integer DEFAULT 3,
    alpha float DEFAULT 0.7, -- Weight for embedding results
    confidence float DEFAULT 0.5,
    metadata_filter jsonb DEFAULT NULL,
    search_language text DEFAULT 'english'
) RETURNS SETOF doc_search_result AS $$
DECLARE
    text_weight float;
    embedding_weight float;
    intermediate_limit integer;
BEGIN
    -- Input validation
    IF k <= 0 THEN
        RAISE EXCEPTION 'k must be greater than 0';
    END IF;

    text_weight := 1.0 - alpha;
    embedding_weight := alpha;
    -- Get more intermediate results than final to allow for better fusion
    intermediate_limit := k * 4;

    RETURN QUERY
    WITH text_results AS (
        SELECT * FROM search_by_text(
            developer_id,
            query_text,
            owner_types,
            owner_ids,
            search_language,
            intermediate_limit,  -- Use larger intermediate limit
            metadata_filter
        )
    ),
    embedding_results AS (
        SELECT * FROM search_by_vector(
            developer_id,
            query_embedding,
            owner_types,
            owner_ids,
            intermediate_limit,  -- Use larger intermediate limit
            confidence,
            metadata_filter
        )
    ),
    all_results AS (
        SELECT DISTINCT doc_id, title, content, metadata, embedding,
               index, owner_type, owner_id
        FROM (
            SELECT * FROM text_results
            UNION
            SELECT * FROM embedding_results
        ) combined
    ),
    scores AS (
        SELECT
            r.doc_id,
            r.title,
            r.content,
            r.metadata,
            r.embedding,
            r.index,
            r.owner_type,
            r.owner_id,
            COALESCE(t.distance, 0.0) as text_score,
            COALESCE(e.distance, 0.0) as embedding_score,
            RANK() OVER (ORDER BY COALESCE(t.distance, 0.0) DESC) as text_rank,
            RANK() OVER (ORDER BY COALESCE(e.distance, 0.0) DESC) as embedding_rank
        FROM all_results r
        LEFT JOIN text_results t ON r.doc_id = t.doc_id
        LEFT JOIN embedding_results e ON r.doc_id = e.doc_id
    ),
    normalized_scores AS (
        SELECT 
            s.*,
            normalized_text_scores[row_number() OVER (ORDER BY s.doc_id)] as norm_text_score,
            normalized_embedding_scores[row_number() OVER (ORDER BY s.doc_id)] as norm_embedding_score
        FROM 
            scores s,
            (SELECT 
                dbsf_normalize(array_agg(text_score ORDER BY doc_id)) as normalized_text_scores,
                dbsf_normalize(array_agg(embedding_score ORDER BY doc_id)) as normalized_embedding_scores
             FROM scores) n
    )
    SELECT
        developer_id,
        doc_id,
        index,
        title,
        content,
        1.0 - (text_weight * norm_text_score + embedding_weight * norm_embedding_score) as distance,
        embedding,
        metadata,
        owner_type,
        owner_id
    FROM normalized_scores
    ORDER BY distance ASC
    LIMIT k;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION search_hybrid IS 'Hybrid search combining text and vector search using Distribution-Based Score Fusion (DBSF)';

COMMIT;