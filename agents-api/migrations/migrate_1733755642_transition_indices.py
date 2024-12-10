# /usr/bin/env python3

MIGRATION_ID = "transition_indices"
CREATED_AT = 1733755642.881131


create_transition_indices = dict(
    up=[
        "::index create executions:execution_id_status_idx { execution_id, status }",
        "::index create executions:execution_id_task_id_idx { execution_id, task_id }",
        "::index create executions:task_id_execution_id_idx { task_id, execution_id }",
        "::index create tasks:task_id_agent_id_idx { task_id, agent_id }",
        "::index create agents:agent_id_developer_id_idx { agent_id, developer_id }",
        "::index create sessions:session_id_developer_id_idx { session_id, developer_id }",
        "::index create docs:owner_id_metadata_doc_id_idx { owner_id, metadata, doc_id }",
        "::index create agents:developer_id_metadata_agent_id_idx { developer_id, metadata, agent_id }",
        "::index create users:developer_id_metadata_user_id_idx { developer_id, metadata, user_id }",
        "::index create transitions:execution_id_type_created_at_idx { execution_id, type, created_at }",
    ],
    down=[
        "::index drop executions:execution_id_status_idx",
        "::index drop executions:execution_id_task_id_idx",
        "::index drop executions:task_id_execution_id_idx",
        "::index drop tasks:task_id_agent_id_idx",
        "::index drop agents:agent_id_developer_id_idx",
        "::index drop sessions:session_id_developer_id_idx",
        "::index drop docs:owner_id_metadata_doc_id_idx",
        "::index drop agents:developer_id_metadata_agent_id_idx",
        "::index drop users:developer_id_metadata_user_id_idx",
        "::index drop transitions:execution_id_type_created_at_idx",
    ],
)


def up(client):
    for q in create_transition_indices["up"]:
        client.run(q)


def down(client):
    for q in create_transition_indices["down"]:
        client.run(q)
