from uuid import UUID
from ...common.protocol.entries import Entry


def entries_summarization_query(
    session_id: UUID, new_entry: Entry, old_entry_ids: list[UUID]
):
    relations = ",\n".join(
        [
            f'[to_uuid("{new_entry.id}")", "summary_of", to_uuid("{old_id}")]'
            for old_id in old_entry_ids
        ]
    )

    return f"""
    {{
        ?[entry_id, session_id, source, role, name, content, token_count, tokenizer, created_at, timestamp] <- [
            [to_uuid("{new_entry.id}"), to_uuid("{session_id}"), "{new_entry.source}", "{new_entry.role}", "{new_entry.name}", "{new_entry.content}", {new_entry.token_count}, "{new_entry.tokenizer}", {new_entry.created_at}, {new_entry.timestamp}]
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
    }}
    {{
        ?[head, relation, tail] <- [
            {relations}
        ]

        :insert entry_relations {{
            head,
            relation,
            tail,
        }}
    }}
    """
