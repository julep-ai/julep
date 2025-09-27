DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[], text, integer, jsonb, float);
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[], text, integer, jsonb);
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[], text, integer);
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[], text);
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[]);

DROP FUNCTION IF EXISTS search_hybrid(UUID, text, vector, TEXT[], UUID[], integer, float, float, jsonb, text, float, integer);
DROP FUNCTION IF EXISTS search_hybrid(UUID, text, vector, TEXT[], UUID[], integer, float, float, jsonb, text);
DROP FUNCTION IF EXISTS search_hybrid(UUID, text, vector, TEXT[], UUID[], integer, float, float, jsonb);
DROP FUNCTION IF EXISTS search_hybrid(UUID, text, vector, TEXT[], UUID[], integer, float, float);
DROP FUNCTION IF EXISTS search_hybrid(UUID, text, vector, TEXT[], UUID[], integer, float);
DROP FUNCTION IF EXISTS search_hybrid(UUID, text, vector, TEXT[], UUID[], integer);
DROP FUNCTION IF EXISTS search_hybrid(UUID, text, vector, TEXT[], UUID[]);

CREATE OR REPLACE FUNCTION search_hybrid (
    p_developer_id UUID,
    p_query_text text,
    p_query_embedding vector(1024),
    p_owner_types TEXT[],
    p_owner_ids UUID[],
    p_k integer DEFAULT 3,
    p_alpha float DEFAULT 0.7,
    p_confidence float DEFAULT 0.5,
    p_metadata_filter jsonb DEFAULT NULL,
    p_search_language text DEFAULT 'english'
)
RETURNS SETOF doc_search_result
LANGUAGE plpgsql AS
$$
DECLARE
    text_weight float := 1.0 - p_alpha;
    embedding_weight float := p_alpha;
    intermediate_limit integer := p_k * 4;
BEGIN
    /*
       1) Get top-N results from text search.
       2) Get top-N results from vector search.
       3) UNION them and pick the highest-distance row per doc_id (DISTINCT ON).
       4) Join those rows back to each sub-result to get text_score and embedding_score.
       5) Aggregate text & embedding scores once, dbsf_normalize once, then map them back by row_number.
    */

    RETURN QUERY
    WITH text_results AS (
        SELECT *
        FROM search_by_text(
            p_developer_id,
            p_query_text,
            p_owner_types,
            p_owner_ids,
            p_search_language,
            intermediate_limit,
            p_metadata_filter
        )
    ),
    embedding_results AS (
        SELECT *
        FROM search_by_vector(
            p_developer_id,
            p_query_embedding,
            p_owner_types,
            p_owner_ids,
            intermediate_limit,
            p_confidence,
            p_metadata_filter
        )
    ),

    -- UNION both sets, pick highest distance row per doc_id
    all_results AS (
        SELECT DISTINCT ON (doc_id)
               developer_id,
               doc_id,
               index,
               title,
               content,
               distance,
               embedding,
               metadata,
               owner_type,
               owner_id
        FROM (
            SELECT * FROM text_results
            UNION ALL
            SELECT * FROM embedding_results
        ) combined
        ORDER BY doc_id, distance DESC
    ),

    -- Gather text_score & embedding_score for each doc
    scores AS (
        SELECT
            a.developer_id,
            a.doc_id,
            a.index,
            a.title,
            a.content,
            a.embedding,
            a.metadata,
            a.owner_type,
            a.owner_id,
            COALESCE(t.distance, 0.0) AS text_score,
            COALESCE(e.distance, 0.0) AS embedding_score
        FROM all_results a
        LEFT JOIN text_results      t ON a.doc_id = t.doc_id
        LEFT JOIN embedding_results e ON a.doc_id = e.doc_id
    ),

    -- Give each row a stable ordering
    scores_ordered AS (
        SELECT
            s.*,
            ROW_NUMBER() OVER (ORDER BY s.doc_id) AS rn
        FROM scores s
    ),

    -- Aggregate all text/embedding scores into arrays
    aggregated AS (
        SELECT
            array_agg(text_score ORDER BY rn)      AS text_scores,
            array_agg(embedding_score ORDER BY rn) AS embedding_scores
        FROM scores_ordered
    ),

    -- Normalize once for each array
    normed_arrays AS (
        SELECT
            dbsf_normalize(text_scores)      AS norm_text_scores,
            dbsf_normalize(embedding_scores) AS norm_embedding_scores
        FROM aggregated
    ),

    -- Join normalized arrays back using row_number
    final AS (
        SELECT
            s.developer_id,
            s.doc_id,
            s.index,
            s.title,
            s.content,
            1.0 - (
                text_weight      * norm_text_scores[s.rn] +
                embedding_weight * norm_embedding_scores[s.rn]
            ) AS distance,
            s.embedding,
            s.metadata,
            s.owner_type,
            s.owner_id
        FROM scores_ordered s
        CROSS JOIN normed_arrays
        ORDER BY distance ASC
        LIMIT p_k
    )
    SELECT * FROM final;
END;
$$;

COMMENT ON FUNCTION search_hybrid IS 'Hybrid search combining text and vector search using Distribution-Based Score Fusion (DBSF)';
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
