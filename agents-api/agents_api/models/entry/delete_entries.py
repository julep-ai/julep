from uuid import UUID

from beartype import beartype


from ..utils import cozo_query
from ...common.protocol.entries import Entry
from ...common.utils.messages import content_to_json


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
def delete_entries(entries: list[Entry]) -> tuple[str, dict]:
    entry_keys = [
        [
            f'to_uuid("{e.id}")',
            f'to_uuid("{e.session_id}")',
            e.source,
            e.role.value if hasattr(e.role, "value") else e.role,
            e.name or None,
            content_to_json(e.content),
            e.token_count,
            e.tokenizer,
            e.created_at,
            e.timestamp,
        ]
        for e in entries
    ]

    query = """
    {
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
        ] <- $entry_keys
        
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

    return (query, {"entry_keys": entry_keys})
