# /usr/bin/env python3

MIGRATION_ID = "extended_tool_relations"
CREATED_AT = 1721576813.383905


drop_agent_functions_hnsw_index = dict(
    up="""
    ::hnsw drop agent_functions:embedding_space
    """,
    down="""
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
)

create_tools_relation = dict(
    up="""
    ?[agent_id, tool_id, type, name, spec, updated_at, created_at] := *agent_functions{
        agent_id, tool_id, name, description, parameters, updated_at, created_at
    }, type = "function",
    spec = {"description": description, "parameters": parameters}

    :create tools {
        agent_id: Uuid,
        tool_id: Uuid,
        =>
        type: String,
        name: String,
        spec: Json,

        updated_at: Float default now(),
        created_at: Float default now(),
    }
    """,
    down="""
    ::remove tools
    """,
)

drop_agent_functions_table = dict(
    up="""
    ::remove agent_functions
    """,
    down="""
    :create agent_functions {
        agent_id: Uuid,
        tool_id: Uuid,
        =>
        name: String,
        description: String,
        parameters: Json,
        embed_instruction: String default 'Transform this tool description for retrieval: ',
        embedding: <F32; 768>? default null,
        updated_at: Float default now(),
        created_at: Float default now(),
    }
    """,
)


queries_to_run = [
    drop_agent_functions_hnsw_index,
    create_tools_relation,
    drop_agent_functions_table,
]


def run(client, *queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


def up(client):
    run(client, *[q["up"] for q in queries_to_run])


def down(client):
    run(client, *[q["down"] for q in reversed(queries_to_run)])
