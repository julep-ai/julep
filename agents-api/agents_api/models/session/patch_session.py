"""This module contains functions for patching session data in the 'cozodb' database using datalog queries."""

from uuid import UUID

import pandas as pd

from ...clients.cozo import client
from ...common.utils.cozo import cozo_process_mutate_data


_fields = [
    "situation",
    "summary",
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
    # Process the update data to prepare it for the query.
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

    metadata = update_data.pop("metadata", {}) or {}

    session_update_cols, session_update_vals = cozo_process_mutate_data(
        {k: v for k, v in update_data.items() if v is not None}
    )

    # Prepare lists of columns for the query.
    session_update_cols_lst = session_update_cols.split(",")
    all_fields_lst = list(set(session_update_cols_lst).union(set(_fields)))
    all_fields = ", ".join(all_fields_lst)
    rest_fields = ", ".join(
        list(
            set(all_fields_lst)
            - set([k for k, v in update_data.items() if v is not None])
        )
    )

    # Construct the datalog query for updating session information.
    session_update_query = f"""
    {{
        input[{session_update_cols}] <- $session_update_vals
        
        ?[{all_fields}, metadata, updated_at] :=
            input[{session_update_cols}],
            *sessions{{
                {rest_fields}, metadata: md, @ "NOW"
            }},
            updated_at = [floor(now()), true],
            metadata = concat(md, $metadata),

        :put sessions {{
            {all_fields}, metadata, updated_at
        }}

        :returning
    }}
    """

    combined_query = "{" + assertion_query + "}" + session_update_query

    return client.run(
        combined_query,
        {
            "session_update_vals": session_update_vals,
            "session_id": str(session_id),
            "developer_id": str(developer_id),
            "metadata": metadata,
        },
    )
