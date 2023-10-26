from ..protocol.entries import Entry
from memory_api.clients.cozo import client


def add_entries(entries: list[Entry], return_result=False) -> list[Entry] | None:
    def _aux_content(e: Entry):
        return e.content.replace('"', "'")

    entries_lst = [
        f'[to_uuid("{e.session_id}"), "{e.role}", "{e.name}", "{_aux_content(e)}", {e.token_count}]'
        for e in entries if e.content
    ]

    if not len(entries_lst):
        return

    entries_query = ",\n".join(entries_lst)

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

    if return_result:
        ids_query = ",\n".join(
            [
                f'[to_uuid("{e.session_id}")]' 
                for e in entries
            ]
        )
        query = f"""
        input[session_id] <- [
            {ids_query}
        ]

        ?[
            session_id,
            entry_id,
            timestamp,
            role,
            name,
            content,
            token_count,
            processed,
            parent_id,
        ] := input[session_id],
            *entries{{
                session_id,
                entry_id,
                timestamp,
                role,
                name,
                content,
                token_count,
                processed,
                parent_id,
            }}
        """

        return [Entry(**row.to_dict()) for _, row in client.run(query).iterrows()]
