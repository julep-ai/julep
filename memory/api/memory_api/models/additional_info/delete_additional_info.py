from typing import Literal
from uuid import UUID


def delete_additional_info_by_id_query(
    owner_type: Literal["user", "agent"], additional_info_id: UUID
):
    additional_info_id = str(additional_info_id)

    return f"""
    {{
        # Delete snippets
        ?[additional_info_id] <- [["{additional_info_id}"]]

        :delete information_snippets {{
            additional_info_id
        }}
    }} {{
        # Delete the additional info
        ?[additional_info_id] <- [["{additional_info_id}"]]

        :delete {owner_type}_additional_info {{
            additional_info_id
        }}
    }}"""


def delete_additional_info_by_owner_query(
    owner_type: Literal["user", "agent"], owner_id: UUID
):
    owner_id = str(owner_id)

    return f"""
    {{
        # Delete snippets
        ?[{owner_type}_id] <- [["{owner_id}"]]

        :delete information_snippets {{
            {owner_type}_id
        }}
    }} {{
        # Delete the additional info
        ?[{owner_type}_id] <- [["{owner_id}"]]

        :delete {owner_type}_additional_info {{
            {owner_type}_id
        }}
    }}"""
