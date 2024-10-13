# /usr/bin/env python3

MIGRATION_ID = "add_forward_tool_calls_option"
CREATED_AT = 1727235852.744035


def run(client, queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


add_forward_tool_calls_option_to_session_query = dict(
    up="""
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
    down="""
    ?[token_budget, context_overflow, developer_id, session_id, updated_at, situation, summary, created_at, metadata, render_templates, token_budget, context_overflow] := *sessions{
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
        token_budget: Int? default null,
        context_overflow: String? default null,
    }
    """,
)


queries = [
    add_forward_tool_calls_option_to_session_query,
]


def up(client):
    run(client, [q["up"] for q in queries])


def down(client):
    run(client, [q["down"] for q in reversed(queries)])
