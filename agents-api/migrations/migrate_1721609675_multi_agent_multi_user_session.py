# /usr/bin/env python3

MIGRATION_ID = "multi_agent_multi_user_session"
CREATED_AT = 1721609675.213755

add_multiple_participants_in_session = dict(
    up="""
    ?[session_id, participant_id, participant_type] :=
        *session_lookup {
            agent_id: participant_id,
            user_id: null,
            session_id,
        }, participant_type = 'agent'

    ?[session_id, participant_id, participant_type] :=
        *session_lookup {
            agent_id,
            user_id: participant_id,
            session_id,
        }, participant_type = 'user',
        participant_id != null

    :replace session_lookup  {
        session_id: Uuid,
        participant_type: String,
        participant_id: Uuid,
    }
    """,
    down="""
    users[user_id, session_id] :=
        *session_lookup {
            session_id,
            participant_type: "user",
            participant_id: user_id,
        }

    agents[agent_id, session_id] :=
        *session_lookup {
            session_id,
            participant_type: "agent",
            participant_id: agent_id,
        }

    ?[agent_id, user_id, session_id] :=
        agents[agent_id, session_id],
        users[user_id, session_id]

    ?[agent_id, user_id, session_id] :=
        agents[agent_id, session_id],
        not users[_, session_id],
        user_id = null

    :replace session_lookup  {
        agent_id: Uuid,
        user_id: Uuid? default null,
        session_id: Uuid,
    }
    """,
)

queries_to_run = [
    add_multiple_participants_in_session,
]


def run(client, *queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


def up(client):
    run(client, *[q["up"] for q in queries_to_run])


def down(client):
    run(client, *[q["down"] for q in reversed(queries_to_run)])
