import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client
from ...common.protocol.entries import Entry
from ...common.utils import json
from ...common.utils.datetime import utcnow


def add_entries_query(
    entries: list[Entry], client: CozoClient = client
) -> pd.DataFrame:
    entries_lst = []
    for e in entries:
        ts = utcnow().timestamp()
        source = json.dumps(e.source)
        role = json.dumps(e.role)
        content: str = (
            e.content if isinstance(e.content, str) else json.dumps(e.content)
        )
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

    if not len(entries_lst):
        return pd.DataFrame(data={})

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
