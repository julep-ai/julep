-- Add fuzzystrmatch extension if not already enabled
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- Add Levenshtein-enhanced similarity function
CREATE OR REPLACE FUNCTION enhanced_similarity(text1 text, text2 text) 
RETURNS float AS $$
DECLARE
    trgm_sim float := similarity(text1, text2);
    lev_dist int;
    norm_lev float;
BEGIN
    -- Only compute Levenshtein for reasonable length strings (performance)
    IF length(text1) <= 50 AND length(text2) <= 50 THEN
        lev_dist := levenshtein_less_equal(text1, text2, 3);
        norm_lev := 1.0 - LEAST(lev_dist::float / 5.0, 1.0);
        -- Combine scores (70% trigram, 30% levenshtein)
        RETURN 0.7 * trgm_sim + 0.3 * norm_lev;
    ELSE
        -- For longer strings, just use trigram similarity
        RETURN trgm_sim;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Add word-level similarity function
CREATE OR REPLACE FUNCTION word_similarity(text1 text, text2 text) 
RETURNS float AS $$
DECLARE
    words1 text[];
    words2 text[];
    i int;
    j int;
    best_match float;
    match_sum float := 0;
    word_count int := 0;
BEGIN
    -- Split into words
    words1 := regexp_split_to_array(lower(text1), '\s+');
    words2 := regexp_split_to_array(lower(text2), '\s+');
    
    -- For each meaningful word in query
    IF words1 IS NOT NULL AND words2 IS NOT NULL THEN
        FOR i IN 1..array_length(words1, 1) LOOP
            -- Only process meaningful words (longer than 2 chars)
            IF length(words1[i]) > 2 THEN
                best_match := 0;
                
                -- Find best match in target content
                FOR j IN 1..array_length(words2, 1) LOOP
                    IF length(words2[j]) > 2 THEN
                        best_match := GREATEST(best_match, similarity(words1[i], words2[j]));
                    END IF;
                END LOOP;
                
                match_sum := match_sum + best_match;
                word_count := word_count + 1;
            END IF;
        END LOOP;
        
        -- Return average word similarity
        IF word_count > 0 THEN
            RETURN match_sum / word_count;
        END IF;
    END IF;
    
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- Create a comprehensive similarity function that combines approaches
CREATE OR REPLACE FUNCTION comprehensive_similarity(title text, content text, query text) 
RETURNS float AS $$
DECLARE
    -- Get trigram score (highest between title and content)
    trgm_sim float := GREATEST(
        enhanced_similarity(title, query),
        enhanced_similarity(content, query)
    );
    
    -- Get word-level score
    word_sim float := GREATEST(
        word_similarity(title, query),
        word_similarity(content, query)
    );
    
    -- Weight factor based on query length - shorter queries need more help
    word_weight float := CASE 
        WHEN length(query) < 10 THEN 0.4
        WHEN length(query) < 20 THEN 0.3
        ELSE 0.2
    END;
    
    -- Complementary weight for trigram
    trgm_weight float := 1.0 - word_weight;
BEGIN    
    -- Weight the different approaches
    RETURN trgm_weight * trgm_sim + word_weight * word_sim;
END;
$$ LANGUAGE plpgsql;

-- Update search_by_text function to use comprehensive similarity
DROP FUNCTION IF EXISTS search_by_text;

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
                comprehensive_similarity(d.title, d.content, $6)::double precision as trigram_score,
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
            AND comprehensive_similarity(d.title, d.content, $6) > $7
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

COMMENT ON FUNCTION search_by_text IS 'Search documents using full-text search and enhanced fuzzy matching with configurable language and filtering options';

-- No need to modify the search_hybrid function as it will automatically use the updated search_by_text function