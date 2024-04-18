from uuid import UUID


from ..utils import cozo_query


@cozo_query
def get_entries_query(
    session_id: UUID, limit: int = 100, offset: int = 0
) -> tuple[str, dict]:
    """
    Constructs and executes a query to retrieve entries from the 'cozodb' database.

    Parameters:
        session_id (UUID): The session ID to filter entries.
        limit (int): The maximum number of entries to return. Defaults to 100.
        offset (int): The offset from which to start returning entries. Defaults to 0.
        client (CozoClient): The CozoClient instance to use for the query.

    Returns:
        pd.DataFrame: The query results as a pandas DataFrame.
    """
    # Construct the query string to select specific fields from the 'entries' relation
    # where the source is either "api_request" or "api_response", sorted by timestamp.
    # The query uses placeholders for session_id, limit, and offset to prevent SQL injection.
    query = """
    {
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
        ] := *entries{
            session_id,
            entry_id,
            role,
            name,
            content,
            source,
            token_count,
            created_at,
            timestamp,
        },
        source in ["api_request", "api_response"],
        session_id = to_uuid($session_id),

        :sort timestamp
        :limit $limit
        :offset $offset
    }"""

    return (query, {"session_id": str(session_id), "limit": limit, "offset": offset})
