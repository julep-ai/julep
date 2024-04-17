"""Module for generating datalog queries to update user information in the 'cozodb' database."""

from uuid import UUID

import pandas as pd

from ...clients.cozo import client
from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow


"""
Generates a datalog query for updating a user's information.

Parameters:
- developer_id (UUID): The UUID of the developer.
- user_id (UUID): The UUID of the user to be updated.
- **update_data: Arbitrary keyword arguments representing the data to be updated.

Returns:
- pd.DataFrame: A pandas DataFrame containing the results of the query execution.
"""


def patch_user_query(developer_id: UUID, user_id: UUID, **update_data) -> pd.DataFrame:
    # Prepare data for mutation by filtering out None values and adding system-generated fields.
    metadata = update_data.pop("metadata", {}) or {}
    user_update_cols, user_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
            "user_id": str(user_id),
            "developer_id": str(developer_id),
            "updated_at": utcnow().timestamp(),
        }
    )

    # Construct the datalog query for updating user information.
    query = f"""
        # update the user
        input[{user_update_cols}] <- $user_update_vals
        
        ?[{user_update_cols}, metadata] := 
            input[{user_update_cols}],
            *users {{
                user_id: to_uuid($user_id),
                metadata: md,
            }},
            metadata = concat(md, $metadata)

        :update users {{
            {user_update_cols}, metadata
        }}
        :returning
    """

    return client.run(
        query,
        {
            "user_update_vals": user_update_vals,
            "metadata": metadata,
            "user_id": str(user_id),
        },
    )
