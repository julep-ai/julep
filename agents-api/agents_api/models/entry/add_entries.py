from ...common.utils import json
from ...common.protocol.entries import Entry
from ...common.utils.datetime import utcnow


def add_entries_query(entries: list[Entry]) -> str:
    def _aux_content(e: Entry):
        return e.content.replace('"', "'")

    entries_lst = []
    for e in entries:
        ts = utcnow().timestamp()
        source = json.dumps(e.source)
        role = json.dumps(e.role)
        name = json.dumps(e.name)
        content = json.dumps(_aux_content(e))
        tokenizer = json.dumps(e.tokenizer)
        if e.content:
            entries_lst.append(
                f'[to_uuid("{e.id}"), to_uuid("{e.session_id}"), {source}, {role}, {name}, {content}, {e.token_count}, {tokenizer}, {ts}, {ts}]'
            )

    if not len(entries_lst):
        return "?[] <- [[]]"

    entries_query = ",\n".join(entries_lst)

    query = f"""
    {{
        ?[entry_id, session_id, source, role, name, content, token_count, tokenizer, created_at, timestamp] <- [
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
            timestamp,
        }}
        :returning
    }}
    """

    return query
