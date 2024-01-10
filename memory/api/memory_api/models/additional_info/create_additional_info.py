import json
from typing import Callable, Literal
from uuid import UUID

from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow


def create_additional_info_query(
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    id: UUID,
    title: str,
    content: str,
    split_fn: Callable[[str], list[str]] = lambda x: x.split("\n\n"),
):
    owner_id = str(owner_id)
    id = str(id)
    created_at: float = utcnow().timestamp()

    snippets = split_fn(content)
    snippet_cols, snippet_rows = [], []

    for snippet_idx, snippet in enumerate(snippets):
        snippet_cols, new_snippet_rows = cozo_process_mutate_data(
            dict(
                additional_info_id=id,
                snippet_idx=snippet_idx,
                title=title,
                snippet=snippet,
            )
        )

        snippet_rows += new_snippet_rows

    return f"""
    {{
        # Create the additional info
        ?[{owner_type}_id, additional_info_id, created_at] <- [[
            to_uuid("{owner_id}"),
            to_uuid("{id}"),
            {created_at},
        ]]

        :insert {owner_type}_additional_info {{
            {owner_type}_id, additional_info_id, created_at
        }}
    }} {{
        # create the snippets
        ?[{snippet_cols}] <- {json.dumps(snippet_rows)}

        :insert information_snippets {{
            {snippet_cols}
        }}
    }} {{
        # return the additional info
        ?[{owner_type}_id, additional_info_id, created_at] <- [[
            to_uuid("{owner_id}"),
            to_uuid("{id}"),
            {created_at},
        ]]
    }}"""
