import json
from typing import Callable, Literal
from uuid import UUID

from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow


def create_docs_query(
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    id: UUID,
    title: str,
    content: str,
    split_fn: Callable[[str], list[str]] = lambda x: x.split("\n\n"),
    metadata: dict = {},
):
    owner_id = str(owner_id)
    id = str(id)
    created_at: float = utcnow().timestamp()

    snippets = split_fn(content)
    snippet_cols, snippet_rows = "", []

    for snippet_idx, snippet in enumerate(snippets):
        snippet_cols, new_snippet_rows = cozo_process_mutate_data(
            dict(
                doc_id=id,
                snippet_idx=snippet_idx,
                title=title,
                snippet=snippet,
            )
        )

        snippet_rows += new_snippet_rows

    return f"""
    {{
        # Create the docs
        ?[{owner_type}_id, doc_id, created_at, metadata] <- [[
            to_uuid("{owner_id}"),
            to_uuid("{id}"),
            {created_at},
            {json.dumps(metadata)},
        ]]

        :insert {owner_type}_docs {{
            {owner_type}_id, doc_id, created_at, metadata,
        }}
    }} {{
        # create the snippets
        ?[{snippet_cols}] <- {json.dumps(snippet_rows)}

        :insert information_snippets {{
            {snippet_cols}
        }}
    }} {{
        # return the docs
        ?[{owner_type}_id, doc_id, created_at, metadata] <- [[
            to_uuid("{owner_id}"),
            to_uuid("{id}"),
            {created_at},
            {json.dumps(metadata)},
        ]]
    }}"""
