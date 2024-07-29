# /usr/bin/env python3

MIGRATION_ID = "rename_executions_arguments_col"
CREATED_AT = 1722107354.988836

rename_arguments_add_metadata_query = dict(
    up="""
    ?[
        task_id,
        execution_id,
        status,
        input,
        session_id,
        created_at,
        updated_at,
        metadata,
    ] :=
        *executions{
            task_id,
            execution_id,
            arguments: input,
            status,
            session_id,
            created_at,
            updated_at,
        }, metadata = {}

    :replace executions {
        task_id: Uuid,
        execution_id: Uuid,
        =>
        status: String default 'queued',
        # one of: "queued", "starting", "running", "awaiting_input", "succeeded", "failed"

        input: Json,
        session_id: Uuid? default null,
        metadata: Json default {},
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
    down="""
    ?[
        task_id,
        execution_id,
        status,
        arguments,
        session_id,
        created_at,
        updated_at,
    ] :=
        *executions{
            task_id,
            execution_id,
            input: arguments,
            status,
            session_id,
            created_at,
            updated_at,
        }

    :replace executions {
        task_id: Uuid,
        execution_id: Uuid,
        =>
        status: String default 'queued',
        # one of: "queued", "starting", "running", "awaiting_input", "succeeded", "failed"

        arguments: Json,
        session_id: Uuid? default null,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
)


def up(client):
    client.run(rename_arguments_add_metadata_query["up"])


def down(client):
    client.run(rename_arguments_add_metadata_query["down"])
