# /usr/bin/env python3

MIGRATION_ID = "session_render_templates"
CREATED_AT = 1714119679.493182

extend_sessions = {
    "up": """
    ?[render_templates, developer_id, session_id, updated_at, situation, summary, created_at, developer_id, metadata] := *sessions{
        session_id,
        updated_at,
        situation,
        summary,
        created_at,
        developer_id
    },
    metadata = {},
    render_templates = false

    :replace sessions {
        developer_id: Uuid,
        session_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        situation: String,
        summary: String? default null,
        created_at: Float default now(),
        metadata: Json default {},
        render_templates: Bool default false,
    }
    """,
    "down": """
    ?[developer_id, session_id, updated_at, situation, summary, created_at, developer_id, metadata] := *sessions{
        session_id,
        updated_at,
        situation,
        summary,
        created_at,
        developer_id
    }, metadata = {}

    :replace sessions {
        developer_id: Uuid,
        session_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        situation: String,
        summary: String? default null,
        created_at: Float default now(),
        metadata: Json default {},
    }
    """,
}


queries_to_run = [
    extend_sessions,
]


def up(client):
    for q in queries_to_run:
        client.run(q["up"])


def down(client):
    for q in reversed(queries_to_run):
        client.run(q["down"])
