BEGIN;

CREATE OR REPLACE FUNCTION search_by_vector (
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
        array_length(owner_types, 1) != array_length(owner_ids, 1) THEN
        RAISE EXCEPTION 'owner_types and owner_ids arrays must have the same length';
    END IF;

    -- Calculate search threshold from confidence
    search_threshold := confidence;

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
                ((1 - (d.embedding <=> $1)) + 1) * 0.5 as distance,
                d.embedding,
                d.metadata,
                doc_owners.owner_type,
                doc_owners.owner_id
            FROM docs_embeddings d
            LEFT JOIN doc_owners ON d.doc_id = doc_owners.doc_id
            WHERE d.developer_id = $7
            AND ((1 - (d.embedding <=> $1)) + 1) * 0.5 >= $2
            %s
            %s
            ORDER BY ((1 - (d.embedding <=> $1)) + 1) * 0.5 DESC
            LIMIT ($3 * 4)  -- Get more candidates than needed
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

COMMIT;