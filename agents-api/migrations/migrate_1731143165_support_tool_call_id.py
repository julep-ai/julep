# /usr/bin/env python3

MIGRATION_ID = "support_tool_call_id"
CREATED_AT = 1731143165.95882

update_entries = {
    "down": """
    ?[
        session_id,
        entry_id,
        source,
        role,
        name,
        content,
        token_count,
        tokenizer,
        created_at,
        timestamp,
    ] := *entries{
        session_id,
        entry_id,
        source,
        role,
        name,
        content: content_string,
        token_count,
        tokenizer,
        created_at,
        timestamp,
    }, content = [{"type": "text", "content": content_string}]

    :replace entries {
        session_id: Uuid,
        entry_id: Uuid default random_uuid_v4(),
        source: String,
        role: String,
        name: String? default null,
        =>
        content: [Json],
        token_count: Int,
        tokenizer: String,
        created_at: Float default now(),
        timestamp: Float default now(),
    }
    """,
    "up": """
    ?[
        session_id,
        entry_id,
        source,
        role,
        name,
        content,
        token_count,
        tokenizer,
        created_at,
        timestamp,
        tool_call_id,
        tool_calls,
    ] := *entries{
        session_id,
        entry_id,
        source,
        role,
        name,
        content: content_string,
        token_count,
        tokenizer,
        created_at,
        timestamp,
    },
    content = [{"type": "text", "content": content_string}],
    tool_call_id = null,
    tool_calls = null

    :replace entries {
        session_id: Uuid,
        entry_id: Uuid default random_uuid_v4(),
        source: String,
        role: String,
        name: String? default null,
        =>
        content: [Json],
        tool_call_id: String? default null,
        tool_calls: [Json]? default null,
        token_count: Int,
        tokenizer: String,
        created_at: Float default now(),
        timestamp: Float default now(),
    }
    """,
}


def up(client):
    client.run(update_entries["up"])


def down(client):
    client.run(update_entries["down"])
