from uuid import UUID


from ..utils import cozo_query


@cozo_query
def get_session_query(
    developer_id: UUID,
    session_id: UUID,
) -> tuple[str, dict]:
    """
    Constructs and executes a datalog query to retrieve session information from the 'cozodb' database.

    Parameters:
        developer_id (UUID): The developer's unique identifier.
        session_id (UUID): The session's unique identifier.

    Returns:
        pd.DataFrame: The result of the query as a pandas DataFrame.
    """
    session_id = str(session_id)
    developer_id = str(developer_id)

    # This query retrieves session information by using `input` to pass parameters,
    # projects specific fields from the `sessions` and `session_lookup` relations,
    # and converts `updated_at` to an integer for easier handling.
    query = """
    input[developer_id, session_id] <- [[
        to_uuid($developer_id),
        to_uuid($session_id),
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
        render_templates,
    ] := input[developer_id, id],
        *sessions{
            developer_id,
            session_id: id,
            situation,
            summary,
            created_at,
            updated_at: validity,
            metadata,
            render_templates,
            @ "NOW"
        },
        *session_lookup{
            agent_id,
            user_id,
            session_id: id,
        }, updated_at = to_int(validity)"""

    return (query, {"session_id": session_id, "developer_id": developer_id})
