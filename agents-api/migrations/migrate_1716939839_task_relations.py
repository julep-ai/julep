# /usr/bin/env python3

MIGRATION_ID = "task_relations"
CREATED_AT = 1716939839.690704


def run(client, queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


create_task_relation_query = dict(
    up="""
    :create tasks {
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
    down="::remove tasks",
)

create_execution_relation_query = dict(
    up="""
    :create executions {
        task_id: Uuid,
        execution_id: Uuid,
        =>
        status: String default 'queued',
        # one of: "queued", "starting", "running", "awaiting_input", "succeeded", "failed"

        arguments: Json,
        session_id: Uuid? default null,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
    down="::remove executions",
)

create_transition_relation_query = dict(
    up="""
    :create transitions {
        execution_id: Uuid,
        transition_id: Uuid,
        =>
        type: String,
        # one of: "finish", "wait", "error", "step"

        from: (String, Int),
        to: (String, Int)?,
        output: Json,

        task_token: String? default null,

        # should store: an Activity Id, a Workflow Id, and optionally a Run Id.
        metadata: Json default {},
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
    down="::remove transitions",
)

queries = [
    create_task_relation_query,
    create_execution_relation_query,
    create_transition_relation_query,
]


def up(client):
    run(client, [q["up"] for q in queries])


def down(client):
    run(client, [q["down"] for q in reversed(queries)])
