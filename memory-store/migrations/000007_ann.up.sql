/*
 * VECTOR SIMILARITY SEARCH WITH DISKANN (Complexity: 8/10)
 * Uses TimescaleDB's vectorizer to convert text into high-dimensional vectors for semantic search.
 * Implements DiskANN (Disk-based Approximate Nearest Neighbor) for efficient similarity search at scale.
 * Includes smart text chunking to handle large documents while preserving context and semantic meaning.
 */

-- Create vector similarity search index using diskann and timescale vectorizer
SELECT
    ai.create_vectorizer (
        source => 'docs',
        destination => 'docs_embeddings',
        embedding => ai.embedding_voyageai ('voyage-3', 1024), -- need to parameterize this
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