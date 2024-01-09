#/usr/bin/env python3

MIGRATION_ID = "developers"
CREATED_AT = 1704699595.546072

def up(client):
    # TODO: add other fields to developers
    create_developers_relation_query = """
    :create developers {
        developer_id: Uuid,
        =>
        name: String,
    }
    """

    update_agents_relation_query = """
    ?[agent_id, name, about, model, created_at, updated_at, developer_id] := *agents{
        agent_id
        =>
        name,
        about,
        model,
        created_at,
        updated_at,
    }, developer_id = rand_uuid_v4()

    :replace agents {
        developer_id: Uuid,
        agent_id: Uuid,
        =>
        name: String,
        about: String,
        model: String default 'julep-ai/samantha-1-turbo',
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """

    update_sessions_relation_query = """
    ?[session_id, updated_at, situation, summary, created_at] := *sessions{
        session_id,
        updated_at
        =>
        situation,
        summary,
        created_at,
    }, developer_id = rand_uuid_v4()

    :replace sessions {
        developer_id: Uuid,
        session_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        situation: String,
        summary: String? default null,
        created_at: Float default now(),
    }
    """

    update_users_relation_query = """
    ?[user_id, name, about, created_at, updated_at, developer_id] := *users{
        user_id
        =>
        name, 
        about, 
        created_at, 
        updated_at,
    }, developer_id = rand_uuid_v4()

    :replace users {
        developer_id: Uuid,
        user_id: Uuid,
        =>
        name: String,
        about: String,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """

    up_queries = [
        create_developers_relation_query,
        update_agents_relation_query,
        update_sessions_relation_query,
        update_users_relation_query,
    ]
    for q in up_queries:
        client.run(q)

def down(client):
    update_agents_relation_query = """
    ?[agent_id, name, about, model, created_at, updated_at] := *agents{
        agent_id
        =>
        name,
        about,
        model,
        created_at,
        updated_at,
    }

    :replace agents {
        agent_id: Uuid,
        =>
        name: String,
        about: String,
        model: String default 'julep-ai/samantha-1-turbo',
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """

    update_sessions_relation_query = """
    ?[session_id, updated_at, situation, summary, created_at] := *sessions{
        session_id,
        updated_at
        =>
        situation,
        summary,
        created_at,
    }

    :replace sessions {
        session_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        situation: String,
        summary: String? default null,
        created_at: Float default now(),
    }
    """

    update_users_relation_query = """
    ?[user_id, name, about, created_at, updated_at] := *users{
        user_id
        =>
        name, 
        about, 
        created_at, 
        updated_at,
    }

    :replace users {
        user_id: Uuid,
        =>
        name: String,
        about: String,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """

    remove_developers_relation_query = """
    ::remove developers
    """

    down_queries = [
        update_agents_relation_query,
        update_sessions_relation_query,
        update_users_relation_query,
        remove_developers_relation_query,
    ]
    for q in down_queries:
        client.run(q)
