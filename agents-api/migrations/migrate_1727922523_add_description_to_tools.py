# /usr/bin/env python3

MIGRATION_ID = "add_description_to_tools"
CREATED_AT = 1727922523.283493


add_description_to_tools = dict(
    up="""
    ?[agent_id, tool_id, type, name, description, spec, updated_at, created_at] := *tools {
        agent_id, tool_id, type, name, spec, updated_at, created_at
    }, description = null

    :replace tools {
        agent_id: Uuid,
        tool_id: Uuid,
        =>
        type: String,
        name: String,
        description: String?,
        spec: Json,

        updated_at: Float default now(),
        created_at: Float default now(),
    }
    """,
    down="""
    ?[agent_id, tool_id, type, name, spec, updated_at, created_at] := *tools {
        agent_id, tool_id, type, name, spec, updated_at, created_at
    }

    :replace tools {
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
)


queries_to_run = [
    add_description_to_tools,
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
