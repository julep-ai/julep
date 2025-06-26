-- Drop the comprehensive similarity function
DROP FUNCTION IF EXISTS comprehensive_similarity;

-- Drop the word similarity function
DROP FUNCTION IF EXISTS fuzzy_word_similarity;

-- Drop the enhanced similarity function
DROP FUNCTION IF EXISTS enhanced_similarity;

-- Drop the additional indexes we created
DROP INDEX IF EXISTS idx_docs_lookup;
DROP INDEX IF EXISTS idx_doc_owners_search;

-- Restore the original search_by_text function from 000031
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[], text, integer, jsonb, float);
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[], text, integer, jsonb);
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[], text, integer);
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[], text);
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[]);

CREATE OR REPLACE FUNCTION search_by_text (
    developer_id UUID,
    query_text text,
    owner_types TEXT[],
    owner_ids UUID[],
    search_language text DEFAULT 'english_unaccent',
    k integer DEFAULT 3,
    metadata_filter jsonb DEFAULT NULL,
    similarity_threshold float DEFAULT 0.6
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

COMMENT ON FUNCTION search_by_text IS 'Search documents using full-text search with configurable language and filtering options';