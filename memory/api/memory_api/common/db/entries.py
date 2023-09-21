from ..protocol.entries import Entry
from memory_api.clients.cozo import client


def add_entries(entries: list[Entry]):
    entries_query = ",\n".join(
        [
            f'[to_uuid("{e.session_id}"), "{e.role}", "{e.name}", "{e.content}", {e.token_count}]' 
            for e in entries
        ]
    )

    query = f"""
    ?[session_id, role, name, content, token_count] <- [
        {entries_query}
    ]

    :put entries {{
        session_id,
        role,
        name,
        content,
        token_count,
    }}
    """

    client.run(query)
