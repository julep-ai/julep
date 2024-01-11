# /usr/bin/env python3

MIGRATION_ID = "tools"
CREATED_AT = 1704892503.302678


def run(client, *queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


agent_instructions_table = dict(
    up="""
    :create agent_instructions {
        agent_id: Uuid,
        instruction_idx: Int,
        =>
        content: String,
        important: Bool default false,
        embed_instruction: String default 'Embed this historical text chunk for retrieval: ',
        embedding: <F32; 768>? default null,
        created_at: Float default now(),
    }
    """,
    down="""
    ::remove agent_instructions
    """,
)

# See: https://github.com/nmslib/hnswlib/blob/master/ALGO_PARAMS.md
agent_instructions_hnsw_index = dict(
    up="""
    ::hnsw create agent_instructions:embedding_space {
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
    ::hnsw drop agent_instructions:embedding_space
    """,
)

agent_functions_table = dict(
    up="""
    :create agent_functions {
        agent_id: Uuid,
        tool_id: Uuid,
        name: String,
        =>
        description: String,
        parameters: Json,
        embed_instruction: String default 'Transform this tool description for retrieval: ',
        embedding: <F32; 768>? default null,
        updated_at: Float default now(),
        created_at: Float default now(),
    }
    """,
    down="""
    ::remove agent_functions
    """,
)


# See: https://github.com/nmslib/hnswlib/blob/master/ALGO_PARAMS.md
agent_functions_hnsw_index = dict(
    up="""
    ::hnsw create agent_functions:embedding_space {
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
    ::hnsw drop agent_functions:embedding_space
    """,
)


queries_to_run = [
    agent_instructions_table,
    agent_instructions_hnsw_index,
    agent_functions_table,
    agent_functions_hnsw_index,
]


def up(client):
    run(client, *[q["up"] for q in queries_to_run])


def down(client):
    run(client, *[q["down"] for q in reversed(queries_to_run)])
