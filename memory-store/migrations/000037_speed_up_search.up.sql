alter table docs add constraint pk_docs primary key (developer_id, doc_id, created_at);
alter table docs add constraint uq_doc_index unique (doc_id, index, created_at);

select ai.drop_vectorizer(id) from ai.vectorizer;

SELECT
    create_hypertable (
        'docs',
        by_range ('created_at', INTERVAL '1 day'),
        if_not_exists => TRUE
    );

SELECT
    ai.create_vectorizer (
        source => 'docs',
        destination => 'docs_embeddings',
        embedding => ai.embedding_openai ('text-embedding-3-large', 1024, 'document'), -- need to parameterize this
        -- actual chunking is managed by the docs table
        -- this is to prevent running out of context window
        chunking => ai.chunking_recursive_character_text_splitter (
            chunk_column => 'content',
            chunk_size => 30000, -- 30k characters ~= 7.5k tokens
            chunk_overlap => 600, -- 600 characters ~= 150 tokens
            separators => ARRAY[ -- tries separators in order
                -- markdown headers
                E'\n#',
                E'\n##',
                E'\n###',
                E'\n---',
                E'\n***',
                -- html tags
                E'</article>', -- Split on major document sections
                E'</div>', -- Split on div boundaries
                E'</section>',
                E'</p>', -- Split on paragraphs
                E'<br>', -- Split on line breaks
                -- other separators
                E'\n\n', -- paragraphs
                '. ',
                '? ',
                '! ',
                '; ', -- sentences (note space after punctuation)
                E'\n', -- line breaks
                ' ' -- words (last resort)
            ]
        ),
        scheduling => ai.scheduling_timescaledb (),
        indexing => ai.indexing_diskann (),
        formatting => ai.formatting_python_template (E'Title: $title\n\n$chunk'),
        processing => ai.processing_default (),
        enqueue_existing => TRUE
    );

alter index idx_docs_metadata|search_tsv|title_trgm|content_trgm set (fastupdate=off);

ALTER TABLE docs ALTER COLUMN title SET STATISTICS 1000;
ALTER TABLE docs ALTER COLUMN content SET STATISTICS 1000;
CREATE INDEX idx_doc_owners_lookup 
ON doc_owners(owner_type, owner_id, doc_id);

SET work_mem = '32MB';

CREATE INDEX idx_doc_owners_agent_lookup ON doc_owners(owner_type, owner_id, doc_id);

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

    SET work_mem = '32MB';

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
    owner_id --,
    -- updated_at,
    -- source
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
    owner_id --,
    -- updated_at,
    -- source
  FROM trgm_scored
)
SELECT *
FROM combined
ORDER BY score DESC -- , updated_at DESC
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
