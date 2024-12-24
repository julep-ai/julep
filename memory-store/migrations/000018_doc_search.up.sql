BEGIN;

-- Create unlogged table for caching embeddings
CREATE UNLOGGED TABLE IF NOT EXISTS embeddings_cache (
    model_input_md5 TEXT NOT NULL,
    embedding vector (1024) NOT NULL,
    CONSTRAINT pk_embeddings_cache PRIMARY KEY (model_input_md5)
);

-- Add comment explaining table purpose
COMMENT ON TABLE embeddings_cache IS 'Unlogged table that caches embedding requests to avoid duplicate API calls';

CREATE
OR REPLACE function embed_with_cache (
    _provider text,
    _model text,
    _input_text text,
    _input_type text DEFAULT NULL,
    _api_key text DEFAULT NULL,
    _api_key_name text DEFAULT NULL
) returns vector (1024) language plpgsql AS $$

-- Try to get cached embedding first
declare
    cached_embedding vector(1024);
    model_input_md5 text;
begin
    if _provider != 'voyageai' then
        raise exception 'Only voyageai provider is supported';
    end if;

    model_input_md5 := md5(_provider || '++' || _model || '++' || _input_text || '++' || _input_type);

    select embedding into cached_embedding
    from embeddings_cache c
    where c.model_input_md5 = model_input_md5;

    if found then
        return cached_embedding;
    end if;

    -- Not found in cache, call AI embedding function
    cached_embedding := ai.voyageai_embed(
        _model,
        _input_text,
        _input_type,
        _api_key,
        _api_key_name
    );

    -- Cache the result
    insert into embeddings_cache (
        model_input_md5,
        embedding
    ) values (
        model_input_md5,
        cached_embedding
    ) on conflict (model_input_md5) do update set embedding = cached_embedding;

    return cached_embedding;
end;
$$;

-- Create a type for the search results if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'doc_search_result'
    ) THEN
        CREATE TYPE doc_search_result AS (
            developer_id uuid,
            doc_id uuid,
            index integer,
            title text,
            content text,
            distance float,
            embedding vector(1024),
            metadata jsonb,
            owner_type text,
            owner_id uuid
        );
    END IF;
END $$;

-- Create the search function
CREATE
OR REPLACE FUNCTION search_by_vector (
    developer_id UUID,
    query_embedding vector (1024),
    owner_types TEXT[],
    owner_ids UUID [],
    k integer DEFAULT 3,
    confidence float DEFAULT 0.5,
    metadata_filter jsonb DEFAULT NULL
) RETURNS SETOF doc_search_result LANGUAGE plpgsql AS $$
DECLARE
    search_threshold float;
    owner_filter_sql text;
    metadata_filter_sql text;
BEGIN
    -- Input validation
    IF k <= 0 THEN
        RAISE EXCEPTION 'k must be greater than 0';
    END IF;

    IF confidence < 0 OR confidence > 1 THEN
        RAISE EXCEPTION 'confidence must be between 0 and 1';
    END IF;

    IF owner_types IS NOT NULL AND owner_ids IS NOT NULL AND
        array_length(owner_types, 1) != array_length(owner_ids, 1) AND
        array_length(owner_types, 1) <= 0 THEN
        RAISE EXCEPTION 'owner_types and owner_ids arrays must have the same length';
    END IF;

    -- Calculate search threshold from confidence
    search_threshold := 1.0 - confidence;

    -- Build owner filter SQL
    owner_filter_sql := '
        AND (
            doc_owners.owner_id = ANY($5::uuid[]) AND doc_owners.owner_type = ANY($4::text[])
        )';

    -- Build metadata filter SQL if provided
    IF metadata_filter IS NOT NULL THEN
        metadata_filter_sql := 'AND d.metadata @> $6';
    ELSE
        metadata_filter_sql := '';
    END IF;

    -- Return search results
    RETURN QUERY EXECUTE format(
        'WITH ranked_docs AS (
            SELECT
                d.developer_id,
                d.doc_id,
                d.index,
                d.title,
                d.content,
                (1 - (d.embedding <=> $1)) as distance,
                d.embedding,
                d.metadata,
                doc_owners.owner_type,
                doc_owners.owner_id
            FROM docs_embeddings d
            LEFT JOIN doc_owners ON d.doc_id = doc_owners.doc_id
            WHERE d.developer_id = $7
            AND 1 - (d.embedding <=> $1) >= $2
            %s
            %s
        )
        SELECT DISTINCT ON (doc_id) *
        FROM ranked_docs
        ORDER BY doc_id, distance DESC
        LIMIT $3',
        owner_filter_sql,
        metadata_filter_sql
    )
    USING
        query_embedding,
        search_threshold,
        k,
        owner_types,
        owner_ids,
        metadata_filter,
        developer_id;


END;
$$;

-- Add helpful comment
COMMENT ON FUNCTION search_by_vector IS 'Search documents by vector similarity with configurable confidence threshold and filtering options';

-- Create the combined embed and search function
CREATE
OR REPLACE FUNCTION embed_and_search_by_vector (
    developer_id UUID,
    query_text text,
    owner_types TEXT[],
    owner_ids UUID [],
    k integer DEFAULT 3,
    confidence float DEFAULT 0.5,
    metadata_filter jsonb DEFAULT NULL,
    embedding_provider text DEFAULT 'voyageai',
    embedding_model text DEFAULT 'voyage-3',
    input_type text DEFAULT 'query',
    api_key text DEFAULT NULL,
    api_key_name text DEFAULT NULL
) RETURNS SETOF doc_search_result LANGUAGE plpgsql AS $$
DECLARE
    query_embedding vector(1024);
BEGIN
    -- First generate embedding for the query text
    query_embedding := embed_with_cache(
        embedding_provider,
        embedding_model,
        query_text,
        input_type,
        api_key,
        api_key_name
    );

    -- Then perform the search using the generated embedding
    RETURN QUERY SELECT * FROM search_by_vector(
        developer_id,
        query_embedding,
        owner_types,
        owner_ids,
        k,
        confidence,
        metadata_filter
    );
END;
$$;

COMMENT ON FUNCTION embed_and_search_by_vector IS 'Convenience function that combines text embedding and vector search in one call';

-- Create the text search function
CREATE
OR REPLACE FUNCTION search_by_text (
    developer_id UUID,
    query_text text,
    owner_types TEXT[],
    owner_ids UUID[],
    search_language text DEFAULT 'english',
    k integer DEFAULT 3,
    metadata_filter jsonb DEFAULT NULL
) RETURNS SETOF doc_search_result LANGUAGE plpgsql AS $$
DECLARE
    owner_filter_sql text;
    metadata_filter_sql text;
    ts_query tsquery;
BEGIN
    -- Input validation
    IF k <= 0 THEN
        RAISE EXCEPTION 'k must be greater than 0';
    END IF;

    IF owner_types IS NOT NULL AND owner_ids IS NOT NULL AND
        array_length(owner_types, 1) != array_length(owner_ids, 1) AND
        array_length(owner_types, 1) <= 0 THEN
        RAISE EXCEPTION 'owner_types and owner_ids arrays must have the same length';
    END IF;

    -- Convert search query to tsquery
    ts_query := websearch_to_tsquery(search_language::regconfig, query_text);

    -- Build owner filter SQL
    owner_filter_sql := '
        AND (
            doc_owners.owner_id = ANY($4::uuid[]) AND doc_owners.owner_type = ANY($3::text[])
        )';


    -- Build metadata filter SQL if provided
    IF metadata_filter IS NOT NULL THEN
        metadata_filter_sql := 'AND d.metadata @> $5';
    ELSE
        metadata_filter_sql := '';
    END IF;

    -- Return search results
    RETURN QUERY EXECUTE format(
        'WITH ranked_docs AS (
            SELECT
                d.developer_id,
                d.doc_id,
                d.index,
                d.title,
                d.content,
                ts_rank_cd(d.search_tsv, $1, 32)::double precision as distance,
                d.embedding,
                d.metadata,
                doc_owners.owner_type,
                doc_owners.owner_id
            FROM docs_embeddings d
            LEFT JOIN doc_owners ON d.doc_id = doc_owners.doc_id
            WHERE d.developer_id = $6
            AND d.search_tsv @@ $1
            %s
            %s
        )
        SELECT DISTINCT ON (doc_id) *
        FROM ranked_docs
        ORDER BY doc_id, distance DESC
        LIMIT $2',
        owner_filter_sql,
        metadata_filter_sql
    )
    USING
        ts_query,
        k,
        owner_types,
        owner_ids,
        metadata_filter,
        developer_id;

END;
$$;

COMMENT ON FUNCTION search_by_text IS 'Search documents using full-text search with configurable language and filtering options';

-- Function to calculate mean of an array
CREATE
OR REPLACE FUNCTION array_mean (arr FLOAT[]) RETURNS float AS $$
    SELECT avg(v) FROM unnest(arr) v;
$$ LANGUAGE SQL;

-- Function to calculate standard deviation of an array
CREATE
OR REPLACE FUNCTION array_stddev (arr FLOAT[]) RETURNS float AS $$
    SELECT stddev(v) FROM unnest(arr) v;
$$ LANGUAGE SQL;

-- DBSF normalization function
CREATE
OR REPLACE FUNCTION dbsf_normalize (scores FLOAT[]) RETURNS FLOAT[] AS $$
DECLARE
    m float;
    sd float;
    m3d float;
    m_3d float;
BEGIN
    -- Handle edge cases
    IF array_length(scores, 1) < 2 THEN
        RETURN scores;
    END IF;

    -- Calculate statistics
    sd := array_stddev(scores);
    IF sd = 0 THEN
        RETURN scores;
    END IF;

    m := array_mean(scores);
    m3d := 3 * sd + m;
    m_3d := m - 3 * sd;

    -- Apply normalization
    RETURN array(
        SELECT (s - m_3d) / (m3d - m_3d)
        FROM unnest(scores) s
    );
END;
$$ LANGUAGE plpgsql;

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
BEGIN
    -- Input validation
    IF k <= 0 THEN
        RAISE EXCEPTION 'k must be greater than 0';
    END IF;

    text_weight := 1.0 - alpha;
    embedding_weight := alpha;

    RETURN QUERY
    WITH text_results AS (
        SELECT * FROM search_by_text(
            developer_id,
            query_text,
            owner_types,
            owner_ids,
            search_language,
            k,
            metadata_filter
        )
    ),
    embedding_results AS (
        SELECT * FROM search_by_vector(
            developer_id,
            query_embedding,
            owner_types,
            owner_ids,
            k,
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
            -- r.developer_id,
            r.doc_id,
            r.title,
            r.content,
            r.metadata,
            r.embedding,
            r.index,
            r.owner_type,
            r.owner_id,
            COALESCE(t.distance, 0.0) as text_score,
            COALESCE(e.distance, 0.0) as embedding_score
        FROM all_results r
        LEFT JOIN text_results t ON r.doc_id = t.doc_id
        LEFT JOIN embedding_results e ON r.doc_id = e.doc_id
    ),
    normalized_scores AS (
        SELECT
            *,
            unnest(dbsf_normalize(array_agg(text_score) OVER ())) as norm_text_score,
            unnest(dbsf_normalize(array_agg(embedding_score) OVER ())) as norm_embedding_score
        FROM scores
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

-- Convenience function that handles embedding generation
CREATE
OR REPLACE FUNCTION embed_and_search_hybrid (
    developer_id UUID,
    query_text text,
    owner_types TEXT[],
    owner_ids UUID [],
    k integer DEFAULT 3,
    alpha float DEFAULT 0.7,
    confidence float DEFAULT 0.5,
    metadata_filter jsonb DEFAULT NULL,
    search_language text DEFAULT 'english',
    embedding_provider text DEFAULT 'voyageai',
    embedding_model text DEFAULT 'voyage-3',
    input_type text DEFAULT 'query',
    api_key text DEFAULT NULL,
    api_key_name text DEFAULT NULL
) RETURNS SETOF doc_search_result AS $$
DECLARE
    query_embedding vector(1024);
BEGIN
    -- Generate embedding for query text
    query_embedding := embed_with_cache(
        embedding_provider,
        embedding_model,
        query_text,
        input_type,
        api_key,
        api_key_name
    );

    -- Perform hybrid search
    RETURN QUERY SELECT * FROM search_hybrid(
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

COMMENT ON FUNCTION embed_and_search_hybrid IS 'Convenience function that combines text embedding generation and hybrid search in one call';

COMMIT;
