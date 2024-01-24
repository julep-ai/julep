#/usr/bin/env python3

MIGRATION_ID = "entries_timestamp"
CREATED_AT = 1706090164.80913


def run(client, *queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


update_entries = {
    "up": """
    ?[
        session_id,
        entry_id,
        source,
        role,
        name,
        content,
        token_count,
        tokenizer,
        created_at,
        timestamp,
    ] := *entries{
        session_id,
        entry_id,
        source,
        role,
        name,
        content,
        token_count,
        tokenizer,
        created_at,
    }, timestamp = created_at

    :replace users {
        session_id: Uuid,
        entry_id: Uuid default random_uuid_v4(),
        source: String,
        role: String,
        name: String? default null,
        =>
        content: String,
        token_count: Int,
        tokenizer: String,
        created_at: Float default now(),
        timestamp: Float default now(),
    }
    """,
    "down": """
    ?[
        session_id,
        entry_id,
        source,
        role,
        name,
        content,
        token_count,
        tokenizer,
        created_at,
    ] := *entries{
        session_id,
        entry_id,
        source,
        role,
        name,
        content,
        token_count,
        tokenizer,
        created_at,
    }

    :replace users {
        session_id: Uuid,
        entry_id: Uuid default random_uuid_v4(),
        source: String,
        role: String,
        name: String? default null,
        =>
        content: String,
        token_count: Int,
        tokenizer: String,
        created_at: Float default now(),
    }
    """
}

queries_to_run = [
    update_entries,
]


def up(client):
    run(client, *[q["up"] for q in queries_to_run])


def down(client):
    run(client, *[q["down"] for q in queries_to_run])
