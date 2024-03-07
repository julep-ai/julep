#/usr/bin/env python3

MIGRATION_ID = "memories"
CREATED_AT = 1709810233.271039


memories = {
    "up": """
    :create memories {
        memory_id: Uuid,
        type: String,  # enum: belief | episode
        =>
        content: String,
        weight: Int,  # range: 0-100
        last_accessed_at: Float? default null,
        timestamp: Float default now(),
        sentiment: Int,
        emotions: String[],
        duration: Float? default null,
        created_at: Float default now(),
        embedding: <F32; 768>? default null,
    }
    """,
    "down": """
    ::remove memories
    """,
}


memory_lookup = {
    "up": """
    :create memory_lookup {
        agent_id: Uuid,
        user_id: Uuid? default null,
        memory_id: Uuid,
    }
    """,
    "down": """
    ::remove memory_lookup
    """
}


memories_hnsw_index = {
    "up": """
    ::hnsw create memories:embedding_space {
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
    "down": """
    ::hnsw drop memories:embedding_space
    """,
}


memories_fts_index = {
    "up": """
    ::fts create memories:fts {
        extractor: content,
        tokenizer: Simple,
        filters: [Lowercase, Stemmer('english'), Stopwords('en')],
    }
    """,
    "down": """
    ::fts drop memories:fts
    """,
}


queries_to_run = [
    memories,
    memory_lookup,
    memories_hnsw_index,
    memories_fts_index,
]


def up(client):
    for q in queries_to_run:
        client.run(q["up"])


def down(client):
    for q in reversed(queries_to_run):
        client.run(q["down"])
