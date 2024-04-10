# /usr/bin/env python3

MIGRATION_ID = "simplify_memories"
CREATED_AT = 1712309841.289588

simplify_memories = {
    "up": """
    ?[
        memory_id,
        content,
        last_accessed_at,
        timestamp,
        sentiment,
        entities,
        created_at,
        embedding,
    ] :=
      *memories {
          memory_id,
          content,
          last_accessed_at,
          timestamp,
          sentiment,
          created_at,
          embedding,
      },
      entities = []

    :replace memories {
        memory_id: Uuid,
        =>
        content: String,
        last_accessed_at: Float? default null,
        timestamp: Float default now(),
        sentiment: Int default 0.0,
        entities: [Json] default [],
        created_at: Float default now(),
        embedding: <F32; 768>? default null,
    }
    """,
    "down": """
    ?[
        memory_id,
        type,
        weight,
        duration,
        emotions,
        content,
        last_accessed_at,
        timestamp,
        sentiment,
        created_at,
        embedding,
    ] :=
      *memories {
          memory_id,
          content,
          last_accessed_at,
          timestamp,
          sentiment,
          created_at,
          embedding,
      },
      type = 'episode',
      weight = 1,
      duration = null,
      emotions = []

    :replace memories {
        memory_id: Uuid,
        type: String,  # enum: belief | episode
        =>
        content: String,
        weight: Int,  # range: 0-100
        last_accessed_at: Float? default null,
        timestamp: Float default now(),
        sentiment: Int,
        emotions: [String],
        duration: Float? default null,
        created_at: Float default now(),
        embedding: <F32; 768>? default null,
    }
    """,
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

drop_memories_hnsw_index = {
    "up": memories_hnsw_index["down"],
    "down": memories_hnsw_index["up"],
}

drop_memories_fts_index = {
    "up": memories_fts_index["down"],
    "down": memories_fts_index["up"],
}

queries_to_run = [
    drop_memories_hnsw_index,
    drop_memories_fts_index,
    simplify_memories,
    memories_hnsw_index,
    memories_fts_index,
]


def up(client):
    for query in queries_to_run:
        client.run(query["up"])


def down(client):
    for query in reversed(queries_to_run):
        client.run(query["down"])
