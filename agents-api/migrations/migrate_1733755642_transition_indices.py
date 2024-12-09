#/usr/bin/env python3

MIGRATION_ID = "transition_indices"
CREATED_AT = 1733755642.881131


create_transition_indices = dict(
    up="""
    ::index create executions:execution_id_status_idx { status, execution_id }
    ::index create executions:execution_id_input_idx { input, execution_id }
    ::index create executions:execution_id_output_idx { output, execution_id }
    ::index create executions:execution_id_error_idx { error, execution_id }
    ::index create executions:execution_id_session_id_idx { session_id, execution_id }
    ::index create executions:execution_id_metadata_idx { metadata, execution_id }

    ::index create agents:developer_id_name_idx { name, developer_id }
    ::index create agents:developer_id_about_idx { about, developer_id }
    ::index create agents:developer_id_instructions_idx { instructions, developer_id }
    ::index create agents:developer_id_model_idx { model, developer_id }
    ::index create agents:developer_id_metadata_idx { metadata, developer_id }

    ::index create developers:developer_id_email_idx { email, developer_id }
    ::index create developers:developer_id_active_idx { active, developer_id }
    ::index create developers:developer_id_tags_idx { tags, developer_id }
    ::index create developers:developer_id_settings_idx { settings, developer_id }

    ::index create transitions:transition_id_type_idx { type, transition_id }
    ::index create transitions:transition_id_current_idx { current, transition_id }
    ::index create transitions:transition_id_next_idx { next, transition_id }
    ::index create transitions:transition_id_output_idx { output, transition_id }
    ::index create transitions:transition_id_task_token_idx { task_token, transition_id }
    ::index create transitions:transition_id_metadata_idx { metadata, transition_id }
    """,
    down="""
    ::index drop executions:execution_id_status_id
    ::index drop executions:execution_id_input_idx
    ::index drop executions:execution_id_output_idx
    ::index drop executions:execution_id_error_idx
    ::index drop executions:execution_id_session_id_idx
    ::index drop executions:execution_id_metadata_idx

    ::index drop agents:developer_id_name_idx
    ::index drop agents:developer_id_about_idx
    ::index drop agents:developer_id_instructions_idx
    ::index drop agents:developer_id_model_idx
    ::index drop agents:developer_id_metadata_idx

    ::index drop developers:developer_id_email_idx
    ::index drop developers:developer_id_active_idx
    ::index drop developers:developer_id_tags_idx
    ::index drop developers:developer_id_settings_idx

    ::index drop transitions:transition_id_type_idx
    ::index drop transitions:transition_id_current_idx
    ::index drop transitions:transition_id_next_idx
    ::index drop transitions:transition_id_output_idx
    ::index drop transitions:transition_id_task_token_idx
    ::index drop transitions:transition_id_metadata_idx
    """,
)


def up(client):
    client.run(create_transition_indices["up"])


def down(client):
    client.run(create_transition_indices["down"])
