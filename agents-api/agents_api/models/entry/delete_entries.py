from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
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


@cozo_query
def delete_entries(entry_ids: list[UUID]) -> tuple[str, dict]:
    query = """
    {
        input[entry_id_str] <- $entry_ids
        
        ?[
            entry_id,
            session_id,
            source,
            role,
            name,
            content,
            token_count,
            tokenizer,
            created_at,
            timestamp,
        ] :=
            input[entry_id_str],
            entry_id = to_uuid(entry_id_str),
            *entries {
                entry_id,
                session_id,
                source,
                role,
                name,
                content,
                token_count,
                tokenizer,
                created_at,
                timestamp,
            }

        :delete entries {
            entry_id,
            session_id,
            source,
            role,
            name,
            content,
            token_count,
            tokenizer,
            created_at,
            timestamp,
        }

        :returning
    }"""

    return (query, {"entry_ids": [[str(id)] for id in entry_ids]})
