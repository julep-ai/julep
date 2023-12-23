from memory_api.common.protocol.entries import Entry
from memory_api.clients.cozo import client


def add_entries(entries: list[Entry], return_result=False) -> list[Entry] | None:
    def _aux_content(e: Entry):
        return e.content.replace('"', "'")
    
    def _aux_tokens_count(e: Entry):
        return e.token_count if e.token_count else len(e.content) // 3.5

    entries_lst = [
        f'[to_uuid("{e.session_id}"), "{e.source}", "{e.role}", "{e.name}", "{_aux_content(e)}", {_aux_tokens_count(e)}, "{e.tokenizer}"]'
        for e in entries
        if e.content
    ]

    if not len(entries_lst):
        return

    entries_query = ",\n".join(entries_lst)

    query = f"""
    ?[session_id, source, role, name, content, token_count, tokenizer] <- [
        {entries_query}
    ], created_at = now()

    :put entries {{
        session_id,
        source,
        role,
        name =>
        content,
        token_count,
        tokenizer,
        created_at,
    }}
    """

    client.run(query)

    if return_result:
        ids_query = ",\n".join([f'[to_uuid("{e.session_id}")]' for e in entries])
        query = f"""
        input[session_id] <- [
            {ids_query}
        ]

        ?[
            session_id,
            entry_id,
            source,
            role,
            name,
            content,
            token_count,
            tokenizer,
            created_at,
        ] := input[session_id],
            *entries{{
                session_id,
                entry_id,
                source,
                role,
                name,
                content,
                token_count,
                tokenizer,
                created_at,
            }}
        """

        return [Entry(**row.to_dict()) for _, row in client.run(query).iterrows()]
