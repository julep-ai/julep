# /usr/bin/env python3

MIGRATION_ID = "metadata"
CREATED_AT = 1709631202.917773


extend_agents = {
    "up": """
    ?[agent_id, name, about, model, created_at, updated_at, developer_id, metadata] := *agents{
        agent_id,
        name,
        about,
        model,
        created_at,
        updated_at,
        developer_id,
    }, metadata = {}

    :replace agents {
        developer_id: Uuid,
        agent_id: Uuid,
        =>
        name: String,
        about: String,
        model: String default 'gpt-4o',
        created_at: Float default now(),
        updated_at: Float default now(),
        metadata: Json default {},
    }
    """,
    "down": """
    ?[agent_id, name, about, model, created_at, updated_at, developer_id] := *agents{
        agent_id,
        name,
        about,
        model,
        created_at,
        updated_at,
        developer_id,
    }

    :replace agents {
        developer_id: Uuid,
        agent_id: Uuid,
        =>
        name: String,
        about: String,
        model: String default 'gpt-4o',
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
}


extend_users = {
    "up": """
    ?[user_id, name, about, created_at, updated_at, developer_id, metadata] := *users{
        user_id,
        name,
        about, 
        created_at, 
        updated_at,
        developer_id,
    }, metadata = {}

    :replace users {
        developer_id: Uuid,
        user_id: Uuid,
        =>
        name: String,
        about: String,
        created_at: Float default now(),
        updated_at: Float default now(),
        metadata: Json default {},
    }
    """,
    "down": """
    ?[user_id, name, about, created_at, updated_at, developer_id] := *users{
        user_id,
        name,
        about, 
        created_at, 
        updated_at,
        developer_id,
    }

    :replace users {
        developer_id: Uuid,
        user_id: Uuid,
        =>
        name: String,
        about: String,
        created_at: Float default now(),
        updated_at: Float default now(),
    }
    """,
}


extend_sessions = {
    "up": """
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
    "down": """
    ?[developer_id, session_id, updated_at, situation, summary, created_at, developer_id] := *sessions{
        session_id,
        updated_at,
        situation,
        summary,
        created_at,
        developer_id
    }

    :replace sessions {
        developer_id: Uuid,
        session_id: Uuid,
        updated_at: Validity default [floor(now()), true],
        =>
        situation: String,
        summary: String? default null,
        created_at: Float default now(),
    }
    """,
}


extend_agent_docs = {
    "up": """
    ?[agent_id, doc_id, created_at, metadata] :=
        *agent_docs{
            agent_id,
            doc_id,
            created_at,
        }, metadata = {}

    :replace agent_docs {
        agent_id: Uuid,
        doc_id: Uuid
        =>
        created_at: Float default now(),
        metadata: Json default {},
    }
    """,
    "down": """
    ?[agent_id, doc_id, created_at] :=
        *agent_docs{
            agent_id,
            doc_id,
            created_at,
        }

    :replace agent_docs {
        agent_id: Uuid,
        doc_id: Uuid
        =>
        created_at: Float default now(),
    }
    """,
}


extend_user_docs = {
    "up": """
    ?[user_id, doc_id, created_at, metadata] :=
        *user_docs{
            user_id,
            doc_id,
            created_at,
        }, metadata = {}

    :replace user_docs {
        user_id: Uuid,
        doc_id: Uuid
        =>
        created_at: Float default now(),
        metadata: Json default {},
    }
    """,
    "down": """
    ?[user_id, doc_id, created_at] :=
        *user_docs{
            user_id,
            doc_id,
            created_at,
        }

    :replace user_docs {
        user_id: Uuid,
        doc_id: Uuid
        =>
        created_at: Float default now(),
    }
    """,
}


queries_to_run = [
    extend_agents,
    extend_users,
    extend_sessions,
    extend_agent_docs,
    extend_user_docs,
]


def up(client):
    for q in queries_to_run:
        client.run(q["up"])


def down(client):
    for q in reversed(queries_to_run):
        client.run(q["down"])
