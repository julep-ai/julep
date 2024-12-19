# /usr/bin/env python3

MIGRATION_ID = "add_recall_options_to_sessions"
CREATED_AT = 1733493650.922383


def run(client, queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


add_recall_options_to_sessions_query = dict(
    up="""
    ?[recall_options, forward_tool_calls, token_budget, context_overflow, developer_id, session_id, updated_at, situation, summary, created_at, metadata, render_templates, token_budget, context_overflow] := *sessions{
        developer_id,
        session_id,
        updated_at,
        situation,
        summary,
        created_at,
        metadata,
        render_templates,
        token_budget,
        context_overflow,
        forward_tool_calls,
    },
    recall_options = {},

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
        forward_tool_calls: Bool? default null,
        recall_options: Json default {},
    }
    """,
    down="""
    ?[forward_tool_calls, token_budget, context_overflow, developer_id, session_id, updated_at, situation, summary, created_at, metadata, render_templates, token_budget, context_overflow] := *sessions{
        developer_id,
        session_id,
        updated_at,
        situation,
        summary,
        created_at,
        metadata,
        render_templates,
        token_budget,
        context_overflow,
    },
    forward_tool_calls = null

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
        forward_tool_calls: Bool? default null,
    }
    """,
)


queries = [
    add_recall_options_to_sessions_query,
]


def up(client):
    run(client, [q["up"] for q in queries])


def down(client):
    run(client, [q["down"] for q in reversed(queries)])
