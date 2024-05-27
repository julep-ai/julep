# /usr/bin/env python3

MIGRATION_ID = "support_multimodal_chatml"
CREATED_AT = 1716847597.155657

update_entries = {
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
        content: content_array,
        token_count,
        tokenizer,
        created_at,
        timestamp,
    }, content = json_to_scalar(get(content_array, 0, ""))

    :replace entries {
        session_id: Uuid,
        entry_id: Uuid default random_uuid_v4(),
        source: String,
        role: String,
        name: String? default null,
        =>
        content: String,
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
