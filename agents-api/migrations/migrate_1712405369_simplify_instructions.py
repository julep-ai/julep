# /usr/bin/env python3

MIGRATION_ID = "simplify_instructions"
CREATED_AT = 1712405369.263776

update_agents_relation_query = dict(
    up="""
    ?[agent_id, name, about, model, created_at, updated_at, developer_id, instructions, metadata] := *agents{
        agent_id,
        name,
        about,
        model,
        created_at,
        updated_at,
        metadata,
    },
    developer_id = rand_uuid_v4(),
    instructions = []

    :replace agents {
        developer_id: Uuid,
        agent_id: Uuid,
        =>
        name: String,
        about: String,
        instructions: [String] default [],
        model: String default 'gpt-4o',
        created_at: Float default now(),
        updated_at: Float default now(),
        metadata: Json default {},
    }
    """,
    down="""
    ?[agent_id, name, about, model, created_at, updated_at, developer_id, metadata] := *agents{
        agent_id,
        name,
        about,
        model,
        created_at,
        updated_at,
        metadata,
    }, developer_id = rand_uuid_v4()

    :replace agents {
        developer_id: Uuid,
        agent_id: Uuid,
        =>
        name: String,
        about: String,
        model: String default 'gpt-4o',
        created_at: Float default now(),
        updated_at: Float default now(),
        metadata: Json default {},
    }
    """,
)

drop_instructions_table = dict(
    down="""
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
    up="""
    ::remove agent_instructions
    """,
)

# See: https://github.com/nmslib/hnswlib/blob/master/ALGO_PARAMS.md
drop_agent_instructions_hnsw_index = dict(
    down="""
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
    up="""
    ::hnsw drop agent_instructions:embedding_space
    """,
)

queries_to_run = [
    drop_agent_instructions_hnsw_index,
    drop_instructions_table,
    update_agents_relation_query,
]


def up(client):
    for query in queries_to_run:
        client.run(query["up"])


def down(client):
    for query in reversed(queries_to_run):
        client.run(query["down"])
