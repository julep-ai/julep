"""This module contains functions for patching session data in the 'cozodb' database using datalog queries."""

from uuid import UUID

import pandas as pd

from ...clients.cozo import client
from ...common.utils.cozo import cozo_process_mutate_data


_fields = [
    "situation",
    "summary",
    "metadata",
    "created_at",
    "session_id",
    "developer_id",
]


def patch_session_query(
    session_id: UUID,
    developer_id: UUID,
    **update_data,
) -> pd.DataFrame:
    """Patch session data in the 'cozodb' database.

    Parameters:
    - session_id (UUID): The unique identifier for the session to be updated.
    - developer_id (UUID): The unique identifier for the developer making the update.
    - **update_data: Arbitrary keyword arguments representing the data to update.

    Returns:
    pd.DataFrame: A pandas DataFrame containing the result of the update operation.
    """
    assertion_query = """
        ?[session_id, developer_id] :=
            *sessions {
                session_id,
                developer_id,
            },
            session_id = to_uuid($session_id),
            developer_id = to_uuid($developer_id),
        # Assertion to ensure the session exists before updating.
        :assert some
    """

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

    # Constructing a datalog query for updating session data based on provided parameters.
    session_update_query = f"""
    {{
        input[{session_update_cols}] <- $session_update_vals
        ids[session_id, developer_id] <- [[$session_id, $developer_id]]
        
        ?[{all_fields}, updated_at] :=
            input[{session_update_cols}],
            ids[session_id, developer_id],
            *sessions{{
                {rest_fields}, @ "NOW"
            }},
            updated_at = [floor(now()), true]

        :update sessions {{
            {all_fields}, updated_at
        }}

        :returning
    }}
    """

    # Execute the constructed datalog query and return the result as a pandas DataFrame.
    query = "{" + assertion_query + "}" + session_update_query

    return client.run(
        query,
        {
            "session_update_vals": session_update_vals,
            "session_id": str(session_id),
            "developer_id": str(developer_id),
        },
    )
