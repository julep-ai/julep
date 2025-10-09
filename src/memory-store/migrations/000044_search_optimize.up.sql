BEGIN;

-- Ensure vectorscale is at least 0.8.0 so label-prefiltered DiskANN indexes are supported.
DO $$
DECLARE
    v_version text;
    v_numeric int[];
BEGIN
    SELECT extversion INTO v_version
    FROM pg_extension
    WHERE extname = 'vectorscale';

    IF v_version IS NULL THEN
        RAISE EXCEPTION 'vectorscale extension is not installed; install >= 0.8.0 before running this migration.';
    END IF;

    v_numeric := string_to_array(regexp_replace(v_version, '[^0-9\.]', '', 'g'), '.')::int[];

    IF coalesce(v_numeric[1], 0) < 0
       OR (coalesce(v_numeric[1], 0) = 0 AND coalesce(v_numeric[2], 0) < 8)
       OR (coalesce(v_numeric[1], 0) = 0 AND coalesce(v_numeric[2], 0) = 8 AND coalesce(v_numeric[3], 0) < 0) THEN
        EXECUTE 'ALTER EXTENSION vectorscale UPDATE TO ''0.8.0''';

        SELECT extversion INTO v_version
        FROM pg_extension
        WHERE extname = 'vectorscale';

        v_numeric := string_to_array(regexp_replace(v_version, '[^0-9\.]', '', 'g'), '.')::int[];

        IF coalesce(v_numeric[1], 0) < 0
           OR (coalesce(v_numeric[1], 0) = 0 AND coalesce(v_numeric[2], 0) < 8)
           OR (coalesce(v_numeric[1], 0) = 0 AND coalesce(v_numeric[2], 0) = 8 AND coalesce(v_numeric[3], 0) < 0) THEN
            RAISE EXCEPTION 'vectorscale extension version % does not support label-aware DiskANN indexes; upgrade to >= 0.8.0.', v_version;
        END IF;
    END IF;
END;
$$;

-- AIDEV-NOTE: pgai 0.6+ needs the refreshed docs vectorizer config; rebuild it if an older one is present.
DO $$
DECLARE
    v_old_id integer;
    v_old_config jsonb;
BEGIN
    SELECT id, config
    INTO v_old_id, v_old_config
    FROM ai.vectorizer
    WHERE source_schema = 'public'
      AND source_table = 'docs'
    ORDER BY id DESC
    LIMIT 1;

    IF v_old_id IS NOT NULL
       AND coalesce(v_old_config -> 'destination' ->> 'target_table', '') <> 'docs_embeddings_store' THEN
        PERFORM ai.drop_vectorizer(v_old_id, drop_all => true);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM ai.vectorizer
        WHERE source_schema = 'public'
          AND source_table = 'docs'
          AND coalesce(config -> 'destination' ->> 'target_table', '') = 'docs_embeddings_store'
    ) THEN
        PERFORM ai.create_vectorizer (
            'public.docs'::regclass,
            name => 'docs_vectorizer',
            grant_to => ai.grant_to('postgres'),
            destination => ai.destination_table(
                target_schema => 'public',
                target_table => 'docs_embeddings_store',
                view_name => 'docs_embeddings'
            ),
            loading => ai.loading_column('content'),
            embedding => ai.embedding_openai('text-embedding-3-large', 1024, 'document'),
            chunking => ai.chunking_recursive_character_text_splitter(
                chunk_size => 30000,
                chunk_overlap => 600,
                separators => ARRAY[
                    E'\n#',
                    E'\n##',
                    E'\n###',
                    E'\n---',
                    E'\n***',
                    E'</article>',
                    E'</div>',
                    E'</section>',
                    E'</p>',
                    E'<br>',
                    E'\n\n',
                    '. ',
                    '? ',
                    '! ',
                    '; ',
                    E'\n',
                    ' '
                ]
            ),
            scheduling => ai.scheduling_timescaledb(),
            indexing => ai.indexing_diskann(),
            formatting => ai.formatting_python_template(E'Title: $title\n\n$chunk'),
            processing => ai.processing_default(),
            enqueue_existing => TRUE,
            if_not_exists => TRUE
        );
    END IF;
END;
$$;

-- Drop any existing DiskANN indexes so we can recreate them with label support.
DO $$
DECLARE
    idx_record record;
BEGIN
    FOR idx_record IN
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'docs_embeddings_store'
          AND indexdef ILIKE '%USING diskann%'
    LOOP
        EXECUTE format('DROP INDEX IF EXISTS %I', idx_record.indexname);
    END LOOP;
END;
$$;

-- Provide a helper for converting UUIDs into vectorscale label arrays when the extension doesn't supply one.
CREATE OR REPLACE FUNCTION public.uuid_to_smallint_labels(p_uuid uuid)
RETURNS smallint[]
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    bytes bytea := uuid_send(p_uuid);
    labels smallint[] := ARRAY[]::smallint[];
    combined integer;
    i integer;
BEGIN
    IF bytes IS NULL THEN
        RETURN NULL;
    END IF;

    FOR i IN 0..7 LOOP
        combined := get_byte(bytes, i * 2) * 256 + get_byte(bytes, i * 2 + 1);
        combined := (combined % 32767) + 1;  -- map into 1..32767
        labels := array_append(labels, combined::smallint);
    END LOOP;

    RETURN labels;
END;
$$;

-- Persist developer labels on the embeddings store so DiskANN can pre-filter candidates.
ALTER TABLE docs_embeddings_store
    ADD COLUMN IF NOT EXISTS developer_labels smallint[]
        GENERATED ALWAYS AS (uuid_to_smallint_labels(developer_id)) STORED;

-- Build a DiskANN index that leverages vectorscale label pre-filtering.
SET LOCAL statement_timeout = '0';
SET LOCAL maintenance_work_mem = '2GB';

CREATE INDEX IF NOT EXISTS idx_docs_embeddings_store_diskann_labels
ON docs_embeddings_store
USING diskann (embedding vector_cosine_ops, developer_labels)
WITH (num_neighbors = 50);

-- Support owner filters by pairing owner type/id with developer/doc for selectivity.
CREATE INDEX IF NOT EXISTS idx_doc_owners_owner_dev_doc
ON doc_owners (owner_type, owner_id, developer_id, doc_id);

-- Replace search_by_text to tighten owner/developer filters and avoid session-wide GUC changes.
DROP FUNCTION IF EXISTS search_by_text(UUID, text, TEXT[], UUID[], text, integer, jsonb, double precision);
CREATE OR REPLACE FUNCTION search_by_text (
    p_developer_id UUID,
    p_query_text text,
    p_owner_types TEXT[],
    p_owner_ids UUID[],
    p_search_language text DEFAULT 'english_unaccent',
    p_k integer DEFAULT 3,
    p_metadata_filter jsonb DEFAULT NULL,
    p_similarity_threshold float DEFAULT NULL
) RETURNS SETOF doc_search_result LANGUAGE plpgsql AS $$
DECLARE
    ts_query tsquery;
BEGIN
    IF p_k <= 0 THEN
        RAISE EXCEPTION 'k must be greater than 0';
    END IF;

    IF COALESCE(array_length(p_owner_types, 1), 0)
       <> COALESCE(array_length(p_owner_ids, 1), 0) THEN
        RAISE EXCEPTION 'owner_types and owner_ids must be the same length';
    END IF;

    ts_query := websearch_to_tsquery(p_search_language::regconfig, p_query_text);

    PERFORM set_config('work_mem', '32MB', true);

    IF p_similarity_threshold IS NULL THEN
        RETURN QUERY
        WITH owner_filter AS (
            SELECT owner_type, owner_id
            FROM unnest(
                COALESCE(p_owner_types, ARRAY[]::text[]),
                COALESCE(p_owner_ids, ARRAY[]::uuid[])
            ) AS of(owner_type, owner_id)
        ),
        fts_results AS (
            SELECT
                d.developer_id,
                d.doc_id,
                d.index,
                d.title,
                d.content,
                ts_rank_cd(d.search_tsv, ts_query, 32)::double precision AS score,
                e.embedding,
                d.metadata,
                of.owner_type,
                of.owner_id
            FROM docs d
            JOIN doc_owners o
              ON o.developer_id = d.developer_id
             AND o.doc_id = d.doc_id
            JOIN owner_filter of
              ON of.owner_type = o.owner_type
             AND of.owner_id = o.owner_id
            LEFT JOIN docs_embeddings e
              ON e.developer_id = d.developer_id
             AND e.doc_id = d.doc_id
             AND e.index = d.index
            WHERE d.developer_id = p_developer_id
              AND d.search_tsv @@ ts_query
              AND (p_metadata_filter IS NULL OR d.metadata @> p_metadata_filter)
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
        LIMIT p_k;
    ELSE
        RETURN QUERY
        WITH owner_filter AS (
            SELECT owner_type, owner_id
            FROM unnest(
                COALESCE(p_owner_types, ARRAY[]::text[]),
                COALESCE(p_owner_ids, ARRAY[]::uuid[])
            ) AS of(owner_type, owner_id)
        ),
        fts_results AS MATERIALIZED (
            SELECT
                d.developer_id,
                d.doc_id,
                d.index,
                d.title,
                d.content,
                ts_rank_cd(d.search_tsv, ts_query, 32)::double precision AS tsv_score,
                NULL::double precision AS trigram_score,
                e.embedding,
                d.metadata,
                of.owner_type,
                of.owner_id,
                d.updated_at,
                1 AS source
            FROM docs d
            JOIN doc_owners o
              ON o.developer_id = d.developer_id
             AND o.doc_id = d.doc_id
            JOIN owner_filter of
              ON of.owner_type = o.owner_type
             AND of.owner_id = o.owner_id
            LEFT JOIN docs_embeddings e
              ON e.developer_id = d.developer_id
             AND e.doc_id = d.doc_id
             AND e.index = d.index
            WHERE d.developer_id = p_developer_id
              AND d.search_tsv @@ ts_query
              AND (p_metadata_filter IS NULL OR d.metadata @> p_metadata_filter)
        ),
        trgm_candidates AS MATERIALIZED (
            SELECT
                d.developer_id,
                d.doc_id,
                d.index,
                d.title,
                d.content,
                d.search_tsv,
                e.embedding,
                d.metadata,
                of.owner_type,
                of.owner_id,
                d.updated_at
            FROM docs d
            JOIN doc_owners o
              ON o.developer_id = d.developer_id
             AND o.doc_id = d.doc_id
            JOIN owner_filter of
              ON of.owner_type = o.owner_type
             AND of.owner_id = o.owner_id
            LEFT JOIN docs_embeddings e
              ON e.developer_id = d.developer_id
             AND e.doc_id = d.doc_id
             AND e.index = d.index
            WHERE d.developer_id = p_developer_id
              AND (p_metadata_filter IS NULL OR d.metadata @> p_metadata_filter)
              AND (d.title %> p_query_text OR d.content %> p_query_text)
              AND NOT EXISTS (
                    SELECT 1
                    FROM fts_results f
                    WHERE f.doc_id = d.doc_id
                      AND f.index = d.index
                      AND f.owner_type = of.owner_type
                      AND f.owner_id = of.owner_id
                )
        ),
        trgm_scored AS (
            SELECT
                t.developer_id,
                t.doc_id,
                t.index,
                t.title,
                t.content,
                NULL::double precision AS tsv_score,
                comprehensive_similarity(t.title, t.content, p_query_text)::double precision AS trigram_score,
                t.embedding,
                t.metadata,
                t.owner_type,
                t.owner_id,
                t.updated_at,
                2 AS source
            FROM trgm_candidates t
            WHERE comprehensive_similarity(t.title, t.content, p_query_text) > p_similarity_threshold
        ),
        combined AS (
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
        LIMIT p_k;
    END IF;
END;
$$;

-- Replace search_by_vector to use label-prefiltered DiskANN results and precise owner pairing.
DROP FUNCTION IF EXISTS search_by_vector(UUID, vector, TEXT[], UUID[], integer, double precision, jsonb);
CREATE OR REPLACE FUNCTION search_by_vector (
    p_developer_id UUID,
    p_query_embedding vector(1024),
    p_owner_types TEXT[],
    p_owner_ids UUID[],
    p_k integer DEFAULT 3,
    p_confidence float DEFAULT 0.0,
    p_metadata_filter jsonb DEFAULT NULL
) RETURNS SETOF doc_search_result LANGUAGE plpgsql AS $$
DECLARE
    search_threshold float;
    label_filter smallint[];
    candidate_limit integer;
BEGIN
    IF p_k <= 0 THEN
        RAISE EXCEPTION 'k must be greater than 0';
    END IF;

    IF p_confidence < -1 OR p_confidence > 1 THEN
        RAISE EXCEPTION 'confidence must be between -1 and 1';
    END IF;

    IF COALESCE(array_length(p_owner_types, 1), 0)
       <> COALESCE(array_length(p_owner_ids, 1), 0) THEN
        RAISE EXCEPTION 'owner_types and owner_ids must be the same length';
    END IF;

    search_threshold := 1.0 - p_confidence;
    label_filter := uuid_to_smallint_labels(p_developer_id);
    candidate_limit := GREATEST(p_k * 8, 40);
    PERFORM set_config('enable_seqscan', 'off', true);
    PERFORM set_config('enable_bitmapscan', 'off', true);

    RETURN QUERY
    WITH owner_filter AS (
        SELECT owner_type, owner_id
        FROM unnest(
            COALESCE(p_owner_types, ARRAY[]::text[]),
            COALESCE(p_owner_ids, ARRAY[]::uuid[])
        ) AS of(owner_type, owner_id)
    ),
    candidates AS (
        SELECT
            emb.developer_id,
            emb.doc_id,
            emb.index,
            emb.embedding,
            (emb.embedding <=> p_query_embedding) AS distance
        FROM docs_embeddings_store emb
        WHERE emb.developer_labels && label_filter
        ORDER BY distance ASC
        LIMIT candidate_limit
    ),
    enriched AS (
        SELECT
            cand.developer_id,
            cand.doc_id,
            cand.index,
            cand.embedding,
            cand.distance,
            d.title,
            d.content,
            d.metadata,
            of.owner_type,
            of.owner_id
        FROM candidates cand
        JOIN docs d
          ON d.developer_id = cand.developer_id
         AND d.doc_id = cand.doc_id
         AND d.index = cand.index
        JOIN doc_owners o
          ON o.developer_id = cand.developer_id
         AND o.doc_id = cand.doc_id
        JOIN owner_filter of
          ON of.owner_type = o.owner_type
         AND of.owner_id = o.owner_id
        WHERE cand.developer_id = p_developer_id
          AND (p_metadata_filter IS NULL OR d.metadata @> p_metadata_filter)
    )
    SELECT DISTINCT ON (doc_id, owner_type, owner_id, index)
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
    FROM enriched
    WHERE p_confidence <= -1 OR distance <= search_threshold
    ORDER BY doc_id, owner_type, owner_id, index, distance
    LIMIT p_k;
END;
$$;

-- Update search_hybrid to align with the refined text/vector functions.
DROP FUNCTION IF EXISTS search_hybrid(UUID, text, vector, TEXT[], UUID[], integer, double precision, double precision, jsonb, text, double precision, integer);
CREATE OR REPLACE FUNCTION search_hybrid (
    p_developer_id UUID,
    p_query_text text,
    p_query_embedding vector (1024),
    p_owner_types TEXT[],
    p_owner_ids UUID [],
    p_k integer DEFAULT 3,
    p_alpha float DEFAULT 0.7,
    p_confidence float DEFAULT 0.5,
    p_metadata_filter jsonb DEFAULT NULL,
    p_search_language text DEFAULT 'english_unaccent',
    p_similarity_threshold float DEFAULT NULL,
    p_k_multiplier integer DEFAULT 5
) RETURNS SETOF doc_search_result
LANGUAGE plpgsql AS $$
DECLARE
    text_weight float := 1.0 - p_alpha;
    embedding_weight float := p_alpha;
    intermediate_limit integer := p_k * p_k_multiplier;
BEGIN
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
            p_metadata_filter,
            p_similarity_threshold
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
    all_results AS (
        SELECT DISTINCT ON (doc_id, owner_type, owner_id, index)
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
        ORDER BY doc_id, owner_type, owner_id, index, distance DESC
    ),
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
        LEFT JOIN text_results t
               ON a.doc_id = t.doc_id
              AND a.index = t.index
              AND a.owner_type = t.owner_type
              AND a.owner_id = t.owner_id
        LEFT JOIN embedding_results e
               ON a.doc_id = e.doc_id
              AND a.index = e.index
              AND a.owner_type = e.owner_type
              AND a.owner_id = e.owner_id
    ),
    scores_ordered AS (
        SELECT
            s.*,
            ROW_NUMBER() OVER (
                ORDER BY s.doc_id, s.owner_type, s.owner_id, s.index
            ) AS rn
        FROM scores s
    ),
    aggregated AS (
        SELECT
            array_agg(text_score ORDER BY rn) AS text_scores,
            array_agg(embedding_score ORDER BY rn) AS embedding_scores
        FROM scores_ordered
    ),
    normed_arrays AS (
        SELECT
            COALESCE(dbsf_normalize(text_scores), ARRAY[]::double precision[]) AS norm_text_scores,
            COALESCE(dbsf_normalize(embedding_scores), ARRAY[]::double precision[]) AS norm_embedding_scores
        FROM aggregated
    ),
    final AS (
        SELECT
            s.developer_id,
            s.doc_id,
            s.index,
            s.title,
            s.content,
            1.0 - (
                text_weight      * COALESCE(norm_text_scores[s.rn], 0.0) +
                embedding_weight * COALESCE(norm_embedding_scores[s.rn], 0.0)
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

COMMIT;
