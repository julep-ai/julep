"""This module contains functions for querying and summarizing entry data in the 'cozodb' database."""

from uuid import UUID


from ...common.protocol.entries import Entry
from ..utils import cozo_query
from ...common.utils import json


@cozo_query
def get_toplevel_entries_query(session_id: UUID) -> tuple[str, dict]:
    """
    Retrieves top-level entries from the database for a given session.

    Parameters:
    - session_id (UUID): The unique identifier for the session.

    Returns:
    - pd.DataFrame: A DataFrame containing the queried top-level entries.
    """

    query = """
        # Construct a datalog query to retrieve entries not summarized by any other entry.
    input[session_id] <- [[to_uuid($session_id)]]
    # Define an input table with the session ID to filter entries related to the specific session.

    # Query to retrieve top-level entries that are not summarized by any other entry, ensuring uniqueness.
    ?[
        entry_id,
        session_id,
        source,
        role,
        name,
        content,
        token_count,
        created_at,
        timestamp,
    ] :=
        input[session_id],
        *entries{
            entry_id,
            session_id,
            source,
            role,
            name,
            content,
            token_count,
            created_at,
            timestamp,
        },
        not *relations {
            relation: "summary_of",
            tail: entry_id,
        }
    
    :sort timestamp
    """

    return (query, {"session_id": str(session_id)})


@cozo_query
def entries_summarization_query(
    session_id: UUID, new_entry: Entry, old_entry_ids: list[UUID]
) -> tuple[str, dict]:
    """
    Inserts a new entry and its summarization relations into the database.

    Parameters:
    - session_id (UUID): The session identifier.
    - new_entry (Entry): The new entry to be inserted.
    - old_entry_ids (list[UUID]): List of entry IDs that the new entry summarizes.

    Returns:
    - pd.DataFrame: A DataFrame containing the result of the insertion operation.
    """

    # Prepare relations data for insertion, marking the new entry as a summary of the old entries.
    relations = [
        [str(new_entry.id), "summary_of", str(old_id)] for old_id in old_entry_ids
    ]
    # Create a list of relations indicating which entries the new entry summarizes.

    # Convert the new entry's source information into JSON format for storage.
    source = json.dumps(new_entry.source)
    role = json.dumps(new_entry.role)
    content = json.dumps(new_entry.content)

    entries = [
        [
            new_entry.id,
            session_id,
            source,
            role,
            new_entry.name or "",
            content,
            new_entry.token_count,
            new_entry.tokenizer,
            new_entry.created_at,
            new_entry.timestamp,
        ]
    ]

    query = """
    {
        ?[entry_id, session_id, source, role, name, content, token_count, tokenizer, created_at, timestamp] <- $entries

        :insert entries {
            entry_id,
            session_id,
            source,
            role,
            name, =>
            content,
            token_count,
            tokenizer,
            created_at,
            timestamp,
        }
    }
    {
        ?[head, relation, tail] <- $relations

        :insert relations {
            head,
            relation,
            tail,
        }
    }
    """

    return (query, {"relations": relations, "entries": entries})
