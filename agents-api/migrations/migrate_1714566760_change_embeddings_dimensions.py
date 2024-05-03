# /usr/bin/env python3

MIGRATION_ID = "change_embeddings_dimensions"
CREATED_AT = 1714566760.731964


change_dimensions = {
    "up": """
    ?[
        doc_id,
        snippet_idx,
        title,
        snippet,
        embed_instruction,
        embedding,
    ] :=
        *information_snippets{
            snippet_idx,
            title,
            snippet,
            embed_instruction,
            embedding,
            doc_id,
        }

    :replace information_snippets {
        doc_id: Uuid,
        snippet_idx: Int,
        =>
        title: String,
        snippet: String,
        embed_instruction: String default 'Encode this passage for retrieval: ',
        embedding: <F32; 1024>? default null,
    }
    """,
    "down": """
    ?[
        doc_id,
        snippet_idx,
        title,
        snippet,
        embed_instruction,
        embedding,
    ] :=
        *information_snippets{
            snippet_idx,
            title,
            snippet,
            embed_instruction,
            embedding,
            doc_id,
        }

    :replace information_snippets {
        doc_id: Uuid,
        snippet_idx: Int,
        =>
        title: String,
        snippet: String,
        embed_instruction: String default 'Encode this passage for retrieval: ',
        embedding: <F32; 768>? default null,
    }
    """,
}

snippets_hnsw_768_index = dict(
    up="""
    ::hnsw create information_snippets:embedding_space {
        fields: [embedding],
        filter: !is_null(embedding),
        dim: 768,
        distance: Cosine,
        m: 64,
        ef_construction: 256,
        extend_candidates: true,
        keep_pruned_connections: false,
    }
    """,
    down="""
    ::hnsw drop information_snippets:embedding_space
    """,
)

drop_snippets_hnsw_768_index = {
    "up": snippets_hnsw_768_index["down"],
    "down": snippets_hnsw_768_index["up"],
}

snippets_hnsw_1024_index = dict(
    up="""
    ::hnsw create information_snippets:embedding_space {
        fields: [embedding],
        filter: !is_null(embedding),
        dim: 1024,
        distance: Cosine,
        m: 64,
        ef_construction: 256,
        extend_candidates: true,
        keep_pruned_connections: false,
    }
    """,
    down="""
    ::hnsw drop information_snippets:embedding_space
    """,
)

drop_snippets_hnsw_1024_index = {
    "up": snippets_hnsw_1024_index["down"],
    "down": snippets_hnsw_1024_index["up"],
}


# See: https://docs.cozodb.org/en/latest/vector.html#full-text-search-fts
information_snippets_fts_index = dict(
    up="""
    ::fts create information_snippets:fts {
        extractor: concat(title, ' ', snippet),
        tokenizer: Simple,
        filters: [Lowercase, Stemmer('english'), Stopwords('en')],
    }
    """,
    down="""
    ::fts drop information_snippets:fts
    """,
)

drop_information_snippets_fts_index = {
    "up": information_snippets_fts_index["down"],
    "down": information_snippets_fts_index["up"],
}


queries_to_run = [
    drop_information_snippets_fts_index,
    drop_snippets_hnsw_768_index,
    change_dimensions,
    snippets_hnsw_1024_index,
    information_snippets_fts_index,
]


def up(client):
    for q in queries_to_run:
        client.run(q["up"])


def down(client):
    for q in reversed(queries_to_run):
        client.run(q["down"])
