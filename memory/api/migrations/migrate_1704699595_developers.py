#/usr/bin/env python3

MIGRATION_ID = "developers"
CREATED_AT = 1704699595.546072

def up(client):
    remove_agents_relation_query = """
    ::remove agents
    """

    remove_sessions_relation_query = """
    ::remove sessions
    """

    remove_users_relation_query = """
    ::remove users
    """

    create_agents_relation_query = """
    :create agents {
        agent_id: Uuid,
        =>
        developer_id: Uuid,
        name: String,
        about: String,
        model: String default 'julep-ai/samantha-1-turbo',
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """

    # TODO: add other fields to developers
    create_developers_relation_query = """
    :create developers {
        developer_id: Uuid,
        =>
        name: String,
    }
    """

    create_sessions_relation_query = """
    :create sessions {
        session_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        developer_id: Uuid,
        situation: String,
        summary: String? default null,
        created_at: Float default now(),
    }
    """

    create_users_relation_query = """
    :create users {
        user_id: Uuid,
        =>
        developer_id: Uuid,
        name: String,
        about: String,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """
    up_queries = [
        remove_agents_relation_query,
        remove_sessions_relation_query,
        remove_users_relation_query,
        create_developers_relation_query,
        create_agents_relation_query,
        create_sessions_relation_query,
        create_users_relation_query,
    ]
    for q in up_queries:
        client.run(q)

def down(client):
    remove_agents_relation_query = """
    ::remove agents
    """

    remove_sessions_relation_query = """
    ::remove sessions
    """

    remove_users_relation_query = """
    ::remove users
    """
    remove_developers_relation_query = """
    ::remove developers
    """

    down_queries = [
        remove_agents_relation_query,
        remove_sessions_relation_query,
        remove_users_relation_query,
        remove_developers_relation_query,
    ]
    for q in down_queries:
        client.run(q)
