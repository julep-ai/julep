# /usr/bin/env python3

MIGRATION_ID = "additional_information"
CREATED_AT = 1704728076.129496


def run(client, *queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


agent_additional_information_table = dict(
    up="""
    :create agent_additional_information {
        agent_id: Uuid,
        additional_info_id: Uuid
        =>
        created_at: Float default now(),
    }
    """,
    down="""
    ::remove agent_additional_information
    """,
)

user_additional_information_table = dict(
    up="""
    :create user_additional_information {
        user_id: Uuid,
        additional_info_id: Uuid
        =>
        created_at: Float default now(),
    }
    """,
    down="""
    ::remove user_additional_information
    """,
)

information_snippets_table = dict(
    up="""
    :create information_snippets {
        additional_info_id: Uuid,
        snippet_idx: Int,
        =>
        title: String,
        snippet: String,
        embed_instruction: String default 'Encode this passage for retrieval: ',
        embedding: <F32; 768>? default null,
    }
    """,
    down="""
    ::remove information_snippets
    """,
)

# See: https://github.com/nmslib/hnswlib/blob/master/ALGO_PARAMS.md
information_snippets_hnsw_index = dict(
    up="""
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
    down="""
    ::hnsw drop information_snippets:embedding_space
    """,
)

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

queries_to_run = [
    agent_additional_information_table,
    user_additional_information_table,
    information_snippets_table,
    information_snippets_hnsw_index,
    information_snippets_fts_index,
]


def up(client):
    run(client, *[q["up"] for q in queries_to_run])


def down(client):
    run(client, *[q["down"] for q in reversed(queries_to_run)])
