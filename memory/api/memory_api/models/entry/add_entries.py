from datetime import datetime
from ...common.protocol.entries import Entry

parenthesize = lambda s: f'"({s})"'


def add_entries_query(entries: list[Entry]) -> str:
    def _aux_content(e: Entry):
        return e.content.replace('"', "'")

    entries_lst = [
        f'[to_uuid("{e.id}"), to_uuid("{e.session_id}"), "{e.source}", "{e.role}", {parenthesize(e.name) if e.name else "null"}, "{_aux_content(e)}", {e.token_count}, "{e.tokenizer}", {datetime.utcnow().timestamp()}]'
        for e in entries
        if e.content
    ]

    if not len(entries_lst):
        return "?[] <- [[]]"

    entries_query = ",\n".join(entries_lst)

    query = f"""
        ?[entry_id, session_id, source, role, name, content, token_count, tokenizer, created_at] <- [
            {entries_query}
        ]

        :insert entries {{
            entry_id,
            session_id,
            source,
            role,
            name, =>
            content,
            token_count,
            tokenizer,
            created_at,
        }}
        :returning
    """

    return query
