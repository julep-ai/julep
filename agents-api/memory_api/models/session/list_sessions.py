from uuid import UUID


def list_sessions_query(developer_id: UUID, limit: int = 100, offset: int = 0):
    return f"""
        input[developer_id] <- [[
            to_uuid("{developer_id}"),
        ]]

        ?[
            agent_id,
            user_id,
            id,
            situation,
            summary,
            updated_at,
            created_at,
        ] :=
            input[developer_id],
            *sessions{{
                developer_id,
                session_id: id,
                situation,
                summary,
                created_at,
                updated_at: validity,
                @ "NOW"
            }},
            *session_lookup{{
                agent_id,
                user_id,
                session_id,
            }}, updated_at = to_int(validity)

        :limit {limit}
        :offset {offset}
        :sort -created_at
    """
