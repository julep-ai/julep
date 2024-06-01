# /usr/bin/env python3

MIGRATION_ID = "token_budget"
CREATED_AT = 1717239610.622555

update_sessions = {
    "up": """
    ?[developer_id, session_id, updated_at, situation, summary, created_at, metadata, render_templates, token_budget, context_overflow] := *sessions{
        developer_id,
        session_id,
        updated_at,
        situation,
        summary,
        created_at,
        metadata,
        render_templates,
    },
    token_budget = null,
    context_overflow = null,

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
        token_budget: Int? default null,
        context_overflow: String? default null,
    }
    """,
    "down": """
    ?[developer_id, session_id, updated_at, situation, summary, created_at, metadata, render_templates] := *sessions{
        developer_id,
        session_id,
        updated_at,
        situation,
        summary,
        created_at,
        metadata,
        render_templates,
    }

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
}


def up(client):
    client.run(update_sessions["up"])


def down(client):
    client.run(update_sessions["down"])
