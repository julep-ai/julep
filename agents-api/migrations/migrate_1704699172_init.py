# /usr/bin/env python3

MIGRATION_ID = "init"
CREATED_AT = 1704699172.673636


def run(client, *queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


def up(client):
    create_agents_relation_query = """
    :create agents {
        agent_id: Uuid,
        =>
        name: String,
        about: String,
        model: String default 'gpt-4o',
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """

    create_model_settings_relation_query = """
    :create agent_default_settings {
        agent_id: Uuid,
        =>
        frequency_penalty: Float default 0.0,
        presence_penalty: Float default 0.0,
        length_penalty: Float default 1.0,
        repetition_penalty: Float default 1.0,
        top_p: Float default 0.95,
        temperature: Float default 0.7,
    }
    """

    create_entries_relation_query = """
    :create entries {
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
    }
    """

    create_sessions_relation_query = """
    :create sessions {
        session_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        situation: String,
        summary: String? default null,
        created_at: Float default now(),
    }
    """

    create_session_lookup_relation_query = """
    :create session_lookup {
        agent_id: Uuid,
        user_id: Uuid? default null,
        session_id: Uuid,
    }
    """

    create_users_relation_query = """
    :create users {
        user_id: Uuid,
        =>
        name: String,
        about: String,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """

    run(
        client,
        create_agents_relation_query,
        create_model_settings_relation_query,
        create_entries_relation_query,
        create_sessions_relation_query,
        create_session_lookup_relation_query,
        create_users_relation_query,
    )


def down(client):
    remove_agents_relation_query = """
    ::remove agents
    """

    remove_model_settings_relation_query = """
    ::remove agent_default_settings
    """

    remove_entries_relation_query = """
    ::remove entries
    """

    remove_sessions_relation_query = """
    ::remove sessions
    """

    remove_session_lookup_relation_query = """
    ::remove session_lookup
    """

    remove_users_relation_query = """
    ::remove users
    """

    run(
        client,
        remove_users_relation_query,
        remove_session_lookup_relation_query,
        remove_sessions_relation_query,
        remove_entries_relation_query,
        remove_model_settings_relation_query,
        remove_agents_relation_query,
    )
