from uuid import UUID

import pandas as pd

from ...clients.cozo import client
from ...common.protocol.entries import Entry
from ...common.utils import json


def get_toplevel_entries_query(session_id: UUID) -> pd.DataFrame:
    query = """
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


def entries_summarization_query(
    session_id: UUID, new_entry: Entry, old_entry_ids: list[UUID]
) -> pd.DataFrame:
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
