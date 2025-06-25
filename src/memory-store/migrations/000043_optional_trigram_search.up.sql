-- Make trigram similarity threshold optional in search functions
-- This allows disabling trigram search by passing NULL

-- Update search_by_text to handle NULL similarity_threshold
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[], text, integer, jsonb, float);

CREATE OR REPLACE FUNCTION search_by_text (
    developer_id UUID,
    query_text text,
    owner_types TEXT[],
    owner_ids UUID[],
    search_language text DEFAULT 'english_unaccent',
    k integer DEFAULT 3,
    metadata_filter jsonb DEFAULT NULL,
    similarity_threshold float DEFAULT NULL  -- Changed to NULL default
) RETURNS SETOF doc_search_result LANGUAGE plpgsql AS $$
DECLARE
    ts_query tsquery;
BEGIN
    IF array_length(owner_types, 1) != array_length(owner_ids, 1) THEN
        RAISE EXCEPTION 'owner_types and owner_ids must be the same length';
    END IF;

    -- Convert query to tsquery
    ts_query := websearch_to_tsquery(search_language::regconfig, query_text);

    SET work_mem = '32MB';

    -- If similarity_threshold is NULL, only do full-text search
    IF similarity_threshold IS NULL THEN
        RETURN QUERY EXECUTE 
'WITH fts_results AS MATERIALIZED (
  SELECT
    d.developer_id,
    d.doc_id,
    d.index,
    d.title,
    d.content,
    ts_rank_cd(d.search_tsv, $1, 32)::double precision AS score,
    e.embedding,
    d.metadata,
    o.owner_type,
    o.owner_id
  FROM docs d
  LEFT JOIN docs_embeddings e
    ON e.developer_id = d.developer_id
    AND e.doc_id = d.doc_id
    AND e.index = d.index
  LEFT JOIN doc_owners o
    ON d.doc_id = o.doc_id
  
  WHERE d.developer_id = $2
    -- Must pass FTS
    AND d.search_tsv @@ $1
    -- Filter by owners if needed
    AND o.owner_type = ANY($3)
    AND o.owner_id   = ANY($4::uuid[])
    AND (($5)::jsonb IS NULL OR d.metadata @> ($5)::jsonb) 
)
SELECT 
    developer_id,
    doc_id,
    index,
    title,
    content,
    score AS distance,
    embedding,
    metadata,
    owner_type,
    owner_id
FROM fts_results
ORDER BY score DESC
LIMIT $6'
        USING
            ts_query,
            developer_id,
            owner_types,
            owner_ids,
            metadata_filter,
            k;
    ELSE
        -- Original behavior with trigram search
        RETURN QUERY EXECUTE 
'WITH fts_results AS MATERIALIZED (
  SELECT
    d.developer_id,
    d.doc_id,
    d.index,
    d.title,
    d.content,
    ts_rank_cd(d.search_tsv, $1, 32)::double precision AS tsv_score,
    NULL::double precision AS trigram_score,
    e.embedding,
    d.metadata,
    o.owner_type,
    o.owner_id,
    d.updated_at,
    /* Mark source=1 for FTS */
    1 AS source
  FROM docs d
  LEFT JOIN docs_embeddings e
    ON e.developer_id = d.developer_id
    AND e.doc_id = d.doc_id
    AND e.index = d.index
  LEFT JOIN doc_owners o
    ON d.doc_id = o.doc_id
  
  WHERE d.developer_id = $2
    -- Must pass FTS
    AND d.search_tsv @@ $1
    -- Filter by owners if needed
    AND o.owner_type = ANY($3)
    AND o.owner_id   = ANY($4::uuid[])
    AND (($5)::jsonb IS NULL OR d.metadata @> ($5)::jsonb) 
),
trgm_candidates AS MATERIALIZED (
  /*
   * Get docs that fail the FTS pass but pass a broad trigram test
   * i.e. (title % :search_text) or (content % :search_text)
   * so it can use your GIN/GIST trigram indexes.
   */
  SELECT
    d.developer_id,
    d.doc_id,
    d.index,
    d.title,
    d.content,
    d.search_tsv,
    e.embedding,
    d.metadata,
    o.owner_type,
    o.owner_id,
    d.updated_at
  FROM docs d
  LEFT JOIN docs_embeddings e
    ON e.developer_id = d.developer_id
    AND e.doc_id = d.doc_id
    AND e.index = d.index
  LEFT JOIN doc_owners o
    ON d.doc_id = o.doc_id
  
  WHERE d.developer_id = $2::uuid
    AND o.owner_type = ANY($3)
    AND o.owner_id   = ANY($4::uuid[])
    AND (($5)::jsonb IS NULL OR d.metadata @> ($5)::jsonb)
    -- A broad trigram match (index-friendly):
    AND (d.title  %> $6
         OR d.content %> $6)
    -- Exclude anything that was already in the FTS set:
    AND NOT EXISTS (
      SELECT 1
      FROM fts_results f
      WHERE f.doc_id = d.doc_id
        AND f.index = d.index
    )
),
trgm_scored AS (
  /*
   * Only now do the heavy comprehensive_similarity check,
   * but only for these trigram candidates.
   */
  SELECT
    t.developer_id,
    t.doc_id,
    t.index,
    t.title,
    t.content,
    NULL::double precision AS tsv_score,
    comprehensive_similarity(t.title, t.content, $6)::double precision AS trigram_score,
    t.embedding,
    t.metadata,
    t.owner_type,
    t.owner_id,
    t.updated_at,
    2 AS source
  FROM trgm_candidates t
  WHERE comprehensive_similarity(t.title, t.content, $6) > $7
),
combined AS (
  /*
   * Union the two sets:
   *   - FTS matches (fts_results) => "score" is tsv_score
   *   - Trigram-only matches => "score" is trigram_score
   */
  SELECT
    developer_id,
    doc_id,
    index,
    title,
    content,
    COALESCE(tsv_score, trigram_score) AS score,
    embedding,
    metadata,
    owner_type,
    owner_id
  FROM fts_results

  UNION ALL

  SELECT
    developer_id,
    doc_id,
    index,
    title,
    content,
    COALESCE(tsv_score, trigram_score) AS score,
    embedding,
    metadata,
    owner_type,
    owner_id
  FROM trgm_scored
)
SELECT *
FROM combined
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
    END IF;
END;
$$;

-- Update search_hybrid to pass NULL similarity_threshold correctly
DROP FUNCTION IF EXISTS search_hybrid(UUID, text, vector, TEXT[], UUID[], integer, float, float, jsonb, text, float, integer);

CREATE OR REPLACE FUNCTION search_hybrid (
    p_developer_id UUID,
    p_query_text text,
    p_query_embedding vector (1024),
    p_owner_types TEXT[],
    p_owner_ids UUID [],
    p_k integer DEFAULT 3,
    p_alpha float DEFAULT 0.7, -- Weight for embedding results
    p_confidence float DEFAULT 0.5,
    p_metadata_filter jsonb DEFAULT NULL,
    p_search_language text DEFAULT 'english_unaccent',
    p_similarity_threshold float DEFAULT NULL,  -- Changed to NULL default
    k_multiplier integer DEFAULT 5
) RETURNS SETOF doc_search_result
LANGUAGE plpgsql AS
$$
DECLARE
    text_weight float := 1.0 - p_alpha;
    embedding_weight float := p_alpha;
    intermediate_limit integer := p_k * k_multiplier;
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
            developer_id => p_developer_id,
            query_text => p_query_text,
            owner_types => p_owner_types,
            owner_ids => p_owner_ids,
            search_language => p_search_language,
            k => intermediate_limit,
            metadata_filter => p_metadata_filter,
            similarity_threshold => p_similarity_threshold
        )
    ),
    embedding_results AS (
        SELECT *
        FROM search_by_vector(
            developer_id => p_developer_id,
            query_embedding => p_query_embedding,
            owner_types => p_owner_types,
            owner_ids => p_owner_ids,
            k => intermediate_limit,
            confidence => p_confidence,
            metadata_filter => p_metadata_filter
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

COMMENT ON FUNCTION search_by_text IS 'Search documents using full-text search with optional trigram fuzzy matching. Pass NULL similarity_threshold to disable trigram search.';
COMMENT ON FUNCTION search_hybrid IS 'Hybrid search combining text and vector search with optional trigram fuzzy matching. Pass NULL similarity_threshold to disable trigram search in text component.';

-- Update embed_and_search_hybrid to use NULL similarity_threshold default
DROP FUNCTION IF EXISTS embed_and_search_hybrid;

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
    similarity_threshold float DEFAULT NULL  -- Changed to NULL default
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

COMMENT ON FUNCTION embed_and_search_hybrid IS 'Convenience function that combines text embedding generation and hybrid search with optional trigram fuzzy matching. Pass NULL similarity_threshold to disable trigram search in text component.';