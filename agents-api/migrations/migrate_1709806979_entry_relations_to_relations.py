#/usr/bin/env python3

MIGRATION_ID = "entry_relations_to_relations"
CREATED_AT = 1709806979.250619


entry_relations_to_relations = {
    "up": """
    ::rename
      entry_relations -> relations,
    """,
    "down": """
    ::rename
      relations -> entry_relations,
    """,
}

queries_to_run = [
    entry_relations_to_relations,
]


def up(client):
    for q in queries_to_run:
        client.run(q["up"])


def down(client):
    for q in reversed(queries_to_run):
        client.run(q["down"])
