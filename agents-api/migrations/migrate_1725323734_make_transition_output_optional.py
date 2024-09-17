# /usr/bin/env python3

MIGRATION_ID = "make_transition_output_optional"
CREATED_AT = 1725323734.591567


def run(client, queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


make_transition_output_optional_query = dict(
    up="""
    ?[
        execution_id,
        transition_id,
        output,
        type,
        current,
        next,
        task_token,
        metadata,
        created_at,
        updated_at,
    ] :=
        *transitions {
            execution_id,
            transition_id,
            output,
            type,
            current,
            next,
            task_token,
            metadata,
            created_at,
            updated_at,
        }

    :replace transitions {
        execution_id: Uuid,
        transition_id: Uuid,
        =>
        type: String,
        current: (String, Int),
        next: (String, Int)?,
        output: Json?,                        # <--- this is the only change; output is now optional
        task_token: String? default null,
        metadata: Json default {},
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
    down="""
    ?[
        execution_id,
        transition_id,
        output,
        type,
        current,
        next,
        task_token,
        metadata,
        created_at,
        updated_at,
    ] :=
        *transitions {
            execution_id,
            transition_id,
            output,
            type,
            current,
            next,
            task_token,
            metadata,
            created_at,
            updated_at,
        }

    :replace transitions {
        execution_id: Uuid,
        transition_id: Uuid,
        =>
        type: String,
        current: (String, Int),
        next: (String, Int)?,
        output: Json,
        task_token: String? default null,
        metadata: Json default {},
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
)


queries = [
    make_transition_output_optional_query,
]


def up(client):
    run(client, [q["up"] for q in queries])


def down(client):
    run(client, [q["down"] for q in reversed(queries)])
