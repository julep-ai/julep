# /usr/bin/env python3

MIGRATION_ID = "rename_information_snippets"
CREATED_AT = 1721678846.468865

rename_information_snippets = dict(
    up="""
    ::rename information_snippets -> snippets
    """,
    down="""
    ::rename snippets -> information_snippets
    """,
)

queries_to_run = [
    rename_information_snippets,
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
