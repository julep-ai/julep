import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client
from ...common.protocol.entries import Entry
from ...common.utils import json
from ...common.utils.datetime import utcnow


def add_entries_query(
    entries: list[Entry], client: CozoClient = client
) -> pd.DataFrame:
    """
    Adds a list of Entry objects and a CozoClient object to a pandas DataFrame.

    Parameters:
        entries (list[Entry]): A list of Entry objects to be processed.
        client (CozoClient): The CozoClient object used for database operations.

    Returns:
        pd.DataFrame: A DataFrame containing the entries data ready for insertion into the 'cozodb' database.
    """
    # Iterate over each entry in the provided list, processing them for database insertion.
    entries_lst = []

    for e in entries:
        ts = utcnow().timestamp()
        source = e.source
        role = e.role
        # Convert the content of each entry to a string, serializing JSON objects.
        content: str = (
            e.content if isinstance(e.content, str) else json.dumps(e.content)
        )
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

    return client.run(query, {"entries_lst": entries_lst})
