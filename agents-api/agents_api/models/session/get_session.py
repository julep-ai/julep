from uuid import UUID


def get_session_query(developer_id: UUID, session_id: UUID):
    session_id = str(session_id)
    developer_id = str(developer_id)

    return f"""
    input[developer_id, session_id] <- [[
        to_uuid("{developer_id}"),
        to_uuid("{session_id}"),
    ]]

    ?[
        agent_id,
        user_id,
        id,
        situation,
        summary,
        updated_at,
        created_at,
        metadata,
    ] := input[developer_id, id],
        *sessions{{
            developer_id,
            session_id: id,
            situation,
            summary,
            created_at,
            updated_at: validity,
            metadata,
            @ "NOW"
        }},
        *session_lookup{{
            agent_id,
            user_id,
            session_id: id,
        }}, updated_at = to_int(validity)"""
