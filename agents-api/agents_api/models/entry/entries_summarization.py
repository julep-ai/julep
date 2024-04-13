"""This module contains functions for querying and summarizing entry data in the 'cozodb' database."""

from uuid import UUID

import pandas as pd

from ...clients.cozo import client
from ...common.protocol.entries import Entry
from ...common.utils import json


"""
Retrieves top-level entries from the database for a given session.

Parameters:
- session_id (UUID): The unique identifier for the session.

Returns:
- pd.DataFrame: A DataFrame containing the queried top-level entries.
"""
def get_toplevel_entries_query(session_id: UUID) -> pd.DataFrame:
    query = """
        # Construct a datalog query to retrieve entries not summarized by any other entry.
    input[session_id] <- [[to_uuid($session_id)]]

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

    return client.run(query, {"session_id": str(session_id)})


"""
Inserts a new entry and its summarization relations into the database.

Parameters:
- session_id (UUID): The session identifier.
- new_entry (Entry): The new entry to be inserted.
- old_entry_ids (list[UUID]): List of entry IDs that the new entry summarizes.

Returns:
- pd.DataFrame: A DataFrame containing the result of the insertion operation.
"""
def entries_summarization_query(
    session_id: UUID, new_entry: Entry, old_entry_ids: list[UUID]
) -> pd.DataFrame:
        # Prepare relations data for insertion, marking the new entry as a summary of the old entries.
    relations = [[str(new_entry.id), "summary_of", str(old_id)] for old_id in old_entry_ids]

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

    return client.run(query, {"relations": relations, "entries": entries})
