from ...common.utils import json
from uuid import UUID

from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow


def update_user_query(developer_id: UUID, user_id: UUID, **update_data) -> str:
    user_update_cols, user_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
            "user_id": user_id,
            "developer_id": developer_id,
            "updated_at": utcnow().timestamp(),
        }
    )

    return f"""
        # update the user
        ?[{user_update_cols}] <- {json.dumps(user_update_vals)}

        :update users {{
            {user_update_cols}
        }}
        :returning
    """
