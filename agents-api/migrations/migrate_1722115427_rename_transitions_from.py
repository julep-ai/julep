# /usr/bin/env python3

MIGRATION_ID = "rename_transitions_from"
CREATED_AT = 1722115427.685346

rename_transitions_from_to_query = dict(
    up="""
    ?[
        execution_id,
        transition_id,
        type,
        current,
        next,
        output,
        task_token,
        metadata,
        created_at,
        updated_at,
    ] := *transitions {
        execution_id,
        transition_id,
        type,
        from: current,
        to: next,
        output,
        task_token,
        metadata,
        created_at,
        updated_at,
    }
 
    :replace transitions {
        execution_id: Uuid,
        transition_id: Uuid,
        =>
        type: String,
        # one of: "finish", "wait", "error", "step"

        current: (String, Int),
        next: (String, Int)?,
        output: Json,

        task_token: String? default null,

        # should store: an Activity Id, a Workflow Id, and optionally a Run Id.
        metadata: Json default {},
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
    down="""
    ?[
        execution_id,
        transition_id,
        type,
        from,
        to,
        output,
        task_token,
        metadata,
        created_at,
        updated_at,
    ] := *transitions {
        execution_id,
        transition_id,
        type,
        current: from,
        next: to,
        output,
        task_token,
        metadata,
        created_at,
        updated_at,
    }
 
    :replace transitions {
        execution_id: Uuid,
        transition_id: Uuid,
        =>
        type: String,
        # one of: "finish", "wait", "error", "step"

        from: (String, Int),
        to: (String, Int)?,
        output: Json,

        task_token: String? default null,

        # should store: an Activity Id, a Workflow Id, and optionally a Run Id.
        metadata: Json default {},
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
)


def up(client):
    client.run(rename_transitions_from_to_query["up"])


def down(client):
    client.run(rename_transitions_from_to_query["down"])
