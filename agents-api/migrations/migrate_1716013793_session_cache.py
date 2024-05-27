# /usr/bin/env python3

MIGRATION_ID = "session_cache"
CREATED_AT = 1716013793.746602


session_cache = dict(
    up="""
    :create session_cache {
        key: String,
        =>
        value: Json,
    }
    """,
    down="""
    ::remove session_cache
    """,
)


queries_to_run = [
    session_cache,
]


def up(client):
    for q in queries_to_run:
        client.run(q["up"])


def down(client):
    for q in reversed(queries_to_run):
        client.run(q["down"])
