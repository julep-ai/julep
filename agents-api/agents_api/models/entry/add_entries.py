import pandas as pd

from beartype import beartype

from ...common.protocol.entries import Entry
from ..utils import cozo_query
from ...common.utils import json
from ...common.utils.datetime import utcnow


@cozo_query
@beartype
def add_entries_query(entries: list[Entry]) -> tuple[str, dict]:
    """
    Parameters:
        entries (list[Entry]): A list of Entry objects to be processed.

    Returns:
        pd.DataFrame: A DataFrame containing the entries data ready for insertion into the 'cozodb' database.
    """
    # Iterate over each entry in the provided list, processing them for database insertion.
    entries_lst = []

    for e in entries:
        ts = utcnow().timestamp()
        source = e.source
        role = e.role

        # Convert the content of each entry to list of text parts if it is a string or a dictionary.
        content: list = []
        if isinstance(e.content, str):
            content = [{"type": "text", "text": e.content}]

        elif isinstance(e.content, dict):
            content = [{"type": "text", "text": json.dumps(e.content, indent=4)}]

        # Append entries with non-empty content to the list for database insertion.
        if e.content:
            entries_lst.append(
                [
                    str(e.id),
                    str(e.session_id),
                    source,
                    role,
                    e.name or "",
                    content,
                    e.token_count,
                    e.tokenizer,
                    ts,
                    ts,
                ]
            )

    # If no entries are provided or all entries have empty content, return an empty DataFrame.
    if not len(entries_lst):
        return pd.DataFrame(data={})

    # Construct a datalog query to insert the processed entries into the 'cozodb' database.
    # Refer to the schema for the 'entries' relation in the README.md for column names and types.
    query = """
    {
        ?[entry_id, session_id, source, role, name, content, token_count, tokenizer, created_at, timestamp] <- $entries_lst

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
        :returning
    }
    """

    return (query, {"entries_lst": entries_lst})
