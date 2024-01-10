from typing import Literal
from uuid import UUID


def get_additional_info_snippets_by_id_query(
    owner_type: Literal["user", "agent"],
    additional_info_id: UUID,
):
    additional_info_id = str(additional_info_id)

    return f"""
        input[additional_info_id] <- [[to_uuid("{additional_info_id}")]]

        ?[
            {owner_type}_id,
            additional_info_id,
            title,
            snippet,
            snippet_idx,
            created_at,
        ] := input[additional_info_id],
            *{owner_type}_additional_info {{
                {owner_type}_id,
                additional_info_id,
                created_at,
            }},
            *information_snippets {{
                additional_info_id,
                snippet_idx,
                title,
                snippet,
            }}
    """
