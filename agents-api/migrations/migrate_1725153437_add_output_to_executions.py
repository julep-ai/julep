# /usr/bin/env python3

MIGRATION_ID = "add_output_to_executions"
CREATED_AT = 1725153437.489542


def run(client, queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


add_output_to_executions_query = dict(
    up="""
    ?[
        task_id,
        execution_id,
        status,
        input,
        session_id,
        created_at,
        updated_at,
        output,
        metadata,
    ] :=
        *executions {
            task_id,
            execution_id,
            status,
            input,
            session_id,
            created_at,
            updated_at,
        },
        output = null,
        metadata = {}

    :replace executions {
        task_id: Uuid,
        execution_id: Uuid,
        =>
        status: String default 'queued',
        # one of: "queued", "starting", "running", "awaiting_input", "succeeded", "failed"

        input: Json,
        output: Json? default null,
        session_id: Uuid? default null,
        metadata: Json default {},
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
    down="""
    ?[
        task_id,
        execution_id,
        status,
        input,
        session_id,
        created_at,
        updated_at,
    ] :=
        *executions {
            task_id,
            execution_id,
            status,
            input,
            session_id,
            created_at,
            updated_at,
        }

    :replace executions {
        task_id: Uuid,
        execution_id: Uuid,
        =>
        status: String default 'queued',
        # one of: "queued", "starting", "running", "awaiting_input", "succeeded", "failed"

        input: Json,
        session_id: Uuid? default null,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
)


queries = [
    add_output_to_executions_query,
]


def up(client):
    run(client, [q["up"] for q in queries])


def down(client):
    run(client, [q["down"] for q in reversed(queries)])
