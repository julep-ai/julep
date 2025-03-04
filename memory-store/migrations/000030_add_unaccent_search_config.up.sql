-- Make sure unaccent extension is installed
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Create a custom text search configuration based on English that uses unaccent
CREATE TEXT SEARCH CONFIGURATION english_unaccent (COPY = english);

-- Set the unaccent dictionary before the english stem dictionary
ALTER TEXT SEARCH CONFIGURATION english_unaccent
    ALTER MAPPING FOR hword, hword_part, word
    WITH unaccent, english_stem;

-- Update the search_tsv function to use this configuration
CREATE OR REPLACE FUNCTION docs_update_search_tsv() RETURNS trigger AS $$
BEGIN
    NEW.search_tsv :=
        setweight(to_tsvector('english_unaccent', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english_unaccent', coalesce(NEW.content, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update the search_by_text function to use english_unaccent configuration
CREATE OR REPLACE FUNCTION search_by_text (
    developer_id UUID,
    query_text text,
    owner_types TEXT[],
    owner_ids UUID[],
    search_language text DEFAULT 'english_unaccent',
    k integer DEFAULT 3,
    metadata_filter jsonb DEFAULT NULL
) RETURNS SETOF doc_search_result LANGUAGE plpgsql AS $$
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

    ts_query := websearch_to_tsquery(search_language::regconfig, query_text);

    RETURN QUERY EXECUTE format(
        'SELECT
            d.developer_id as developer_id,
            d.doc_id as doc_id,
            d.index as index,
            d.title as title,
            d.content as content,
            ts_rank_cd(d.search_tsv, $1, 32)::double precision as distance,
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
        %s
        %s
        ORDER BY distance DESC
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

-- Update existing docs with the new text search configuration
UPDATE docs
SET search_tsv = 
    setweight(to_tsvector('english_unaccent', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english_unaccent', coalesce(content, '')), 'B'); 