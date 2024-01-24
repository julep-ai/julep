#/usr/bin/env python3

MIGRATION_ID = "entry_relations"
CREATED_AT = 1706092435.462968

def run(client, *queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


entry_relations = {
    "up": """
    :create entry_relations {
        head: Uuid,
        relation: String,
        tail: Uuid,
    }
    """,
    "down": """
    ::remove entry_relations
    """
}

queries_to_run = [
    entry_relations,
]


def up(client):
    run(client, *[q["up"] for q in queries_to_run])


def down(client):
    run(client, *[q["down"] for q in queries_to_run])
