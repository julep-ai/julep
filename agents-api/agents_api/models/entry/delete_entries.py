from uuid import UUID


from ..utils import cozo_query


@cozo_query
def delete_entries_query(session_id: UUID) -> tuple[str, dict]:
    """
    Constructs and returns a datalog query for deleting entries associated with a given session ID from the 'cozodb' database.

    Parameters:
    - session_id (UUID): The unique identifier of the session whose entries are to be deleted.

    Returns:
    - pd.DataFrame: A DataFrame containing the results of the deletion query.
    """
    query = """
    {
        input[session_id] <- [[
            to_uuid($session_id),
        ]]

        ?[
            session_id,
            entry_id,
            role,
            name,
            content,
            source,
            token_count,
            created_at,
            timestamp,
        ] := input[session_id],
            *entries{
                session_id,
                entry_id,
                role,
                name,
                content,
                source,
                token_count,
                created_at,
                timestamp,
            }
        
        :delete entries {
            session_id,
            entry_id,
            role,
            name,
            content,
            source,
            token_count,
            created_at,
            timestamp,
        }
    }"""

    return (query, {"session_id": str(session_id)})
