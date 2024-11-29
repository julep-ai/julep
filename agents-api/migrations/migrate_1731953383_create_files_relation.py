# /usr/bin/env python3

MIGRATION_ID = "create_files_relation"
CREATED_AT = 1731953383.258172

create_files_query = dict(
    up="""
    :create files {
        developer_id: Uuid,
        file_id: Uuid,
        =>
        name: String,
        description: String default "",
        mime_type: String? default null,
        size: Int,
        hash: String,
        created_at: Float default now(),
    }
    """,
    down="::remove files",
)


def up(client):
    client.run(create_files_query["up"])


def down(client):
    client.run(create_files_query["down"])
