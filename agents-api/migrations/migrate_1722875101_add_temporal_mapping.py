# /usr/bin/env python3

MIGRATION_ID = "add_temporal_mapping"
CREATED_AT = 1722875101.262791


def run(client, queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


create_temporal_executions_lookup = dict(
    up="""
    :create temporal_executions_lookup {
        execution_id: Uuid,
        id: String,
        =>
        run_id: String?,
        first_execution_run_id: String?,
        result_run_id: String?,
        created_at: Float default now(),
    }
    """,
    down="::remove temporal_executions_lookup",
)

queries = [
    create_temporal_executions_lookup,
]


def up(client):
    run(client, [q["up"] for q in queries])


def down(client):
    run(client, [q["down"] for q in reversed(queries)])
