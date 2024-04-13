from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client

from ...common.utils.cozo import cozo_process_mutate_data


def update_user_query(
    developer_id: UUID, user_id: UUID, client: CozoClient = client, **update_data
) -> pd.DataFrame:
    user_id = str(user_id)
    developer_id = str(developer_id)
    user_update_cols, user_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
            "user_id": user_id,
            "developer_id": developer_id,
        }
    )

    assertion_query = f"""
        input[developer_id, user_id] <- [[
            to_uuid("{developer_id}"), to_uuid("{user_id}"),
        ]]

        ?[developer_id, user_id] :=
            input[developer_id, user_id],
            *users {{
                developer_id,
                user_id,
            }}

        :assert some
    """

    query = f"""
        # update the user
        input[{user_update_cols}] <- $user_update_vals
        original[created_at] := *users{{
            developer_id: to_uuid($developer_id),
            user_id: to_uuid($user_id),
            created_at,
        }},

        ?[created_at, updated_at, {user_update_cols}] :=
            input[{user_update_cols}],
            original[created_at],
            updated_at = now(),

        :put users {{
            created_at,
            updated_at,
            {user_update_cols}
        }}
        :returning
    """

    query = "{" + assertion_query + "} {" + query + "}"

    return client.run(
        query,
        {
            "user_update_vals": user_update_vals,
            "developer_id": developer_id,
            "user_id": user_id,
        },
    )
