# /usr/bin/env python3

MIGRATION_ID = "task_tool_ref_by_name"
CREATED_AT = 1721609661.768934


# - add metadata
# - add inherit_tools bool
# - rename tools_available to tools
update_tasks_relation = dict(
    up="""
    ?[
        agent_id,
        task_id,
        updated_at_ms,
        name,
        description,
        input_schema,
        inherit_tools,
        workflows,
        created_at,
        metadata,
    ] := *tasks {
        agent_id,
        task_id,
        updated_at_ms,
        name,
        description,
        input_schema,
        workflows,
        created_at,
    },
    metadata = {},
    inherit_tools = true

    :replace tasks {
        agent_id: Uuid,
        task_id: Uuid,
        updated_at_ms: Validity default [floor(now() * 1000), true],
        =>
        name: String,
        description: String? default null,
        input_schema: Json,
        tools: [Json] default [],
        inherit_tools: Bool default true,
        workflows: [Json],
        created_at: Float default now(),
        metadata: Json default {},
    }
    """,
    down="""
    ?[
        agent_id,
        task_id,
        updated_at_ms,
        name,
        description,
        input_schema,
        workflows,
        created_at,
    ] := *tasks {
        agent_id,
        task_id,
        updated_at_ms,
        name,
        description,
        input_schema,
        workflows,
        created_at,
    }

    :replace tasks {
        agent_id: Uuid,
        task_id: Uuid,
        updated_at_ms: Validity default [floor(now() * 1000), true],
        =>
        name: String,
        description: String? default null,
        input_schema: Json,
        tools_available: [Uuid] default [],
        workflows: [Json],
        created_at: Float default now(),
    }
    """,
)

queries_to_run = [
    update_tasks_relation,
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
