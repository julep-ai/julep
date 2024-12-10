# /usr/bin/env python3

MIGRATION_ID = "transition_indices"
CREATED_AT = 1733755642.881131


create_transition_indices = dict(
    up="""
    ::index create executions:execution_id_status_idx { status, execution_id }
    ::index create transitions:execution_id_type_idx { type, transition_id }
    ::index create executions:execution_id_metadata_idx { metadata, execution_id }
    """,
    down="""
    ::index drop executions:execution_id_status_idx
    ::index drop transitions:execution_id_type_idx
    ::index drop executions:execution_id_metadata_idx
    """,
)


def up(client):
    client.run(create_transition_indices["up"])


def down(client):
    client.run(create_transition_indices["down"])
