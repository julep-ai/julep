import json
from uuid import UUID

from ...common.utils.cozo import cozo_process_mutate_data


_fields = [
    "situation",
    "summary",
    "metadata",
    "created_at",
    "session_id",
    "developer_id",
]


def update_session_query(
    session_id: UUID,
    developer_id: UUID,
    **update_data,
) -> str:
    session_id = str(session_id)
    developer_id = str(developer_id)

    session_update_cols, session_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
        }
    )

    session_update_cols_lst = session_update_cols.split(",")
    all_fields_lst = list(set(session_update_cols_lst).union(set(_fields)))
    all_fields = ", ".join(all_fields_lst)
    rest_fields = ", ".join(
        list(
            set(all_fields_lst)
            - set([k for k, v in update_data.items() if v is not None])
        )
    )

    session_update_query = f"""
    {{
        input[{session_update_cols}, session_id, developer_id] <- [
            [{json.dumps(session_update_vals[0]).strip("[]")}, to_uuid("{session_id}"), to_uuid("{developer_id}")]
        ]
        
        ?[{all_fields}, updated_at] :=
            input[{session_update_cols}, session_id, developer_id],
            *sessions{{
                {rest_fields}, @ "NOW"
            }},
            updated_at = [floor(now()), true]

        :put sessions {{
            {all_fields}, updated_at
        }}

        :returning
    }}
    """

    return session_update_query
