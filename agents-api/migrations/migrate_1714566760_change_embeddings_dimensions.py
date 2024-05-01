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
            additional_info_id: doc_id,
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
            additional_info_id: doc_id,
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

information_snippets_hnsw_index = dict(
    up="""
    ::hnsw create information_snippets:embedding_space {
        fields: [embedding],
        filter: !is_null(embedding),
        dim: 1024,
        distance: Cosine,
        m: 64,
        ef_construction: 256,
        extend_candidates: false,
        keep_pruned_connections: false,
    }
    """,
    down="""

    ::hnsw create information_snippets:embedding_space {
        fields: [embedding],
        filter: !is_null(embedding),
        dim: 768,
        distance: Cosine,
        m: 64,
        ef_construction: 256,
        extend_candidates: false,
        keep_pruned_connections: false,
    }
    """,
)

drop_index = {
    "up": """
    ::hnsw drop information_snippets:embedding_space
    """,
    "down": """
    ::hnsw drop information_snippets:embedding_space
    """,
}


queries_to_run = [
    drop_index,
    change_dimensions,
    information_snippets_hnsw_index,
]


def up(client):
    for q in queries_to_run:
        client.run(q["up"])


def down(client):
    for q in reversed(queries_to_run):
        client.run(q["down"])
