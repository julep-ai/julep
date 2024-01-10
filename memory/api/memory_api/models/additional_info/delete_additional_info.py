from typing import Literal
from uuid import UUID


def delete_additional_info_by_id_query(
    owner_type: Literal["user", "agent"], owner_id: UUID, additional_info_id: UUID
):
    owner_id = str(owner_id)
    additional_info_id = str(additional_info_id)

    return f"""
    {{
        # Delete snippets
        input[additional_info_id] <- [[to_uuid("{additional_info_id}")]]
        ?[additional_info_id, snippet_idx] :=
            input[additional_info_id],
            *information_snippets {{
                additional_info_id,
                snippet_idx,
            }}

        :delete information_snippets {{
            additional_info_id,
            snippet_idx
        }}
    }} {{
        # Delete the additional info
        ?[additional_info_id, {owner_type}_id] <- [[
            to_uuid("{additional_info_id}"),
            to_uuid("{owner_id}"),
        ]]

        :delete {owner_type}_additional_info {{
            additional_info_id,
            {owner_type}_id,
        }}
        :returning
    }}"""
