"""This module contains functions for querying session data from the 'cozodb' database."""

from beartype import beartype

from typing import Any
from uuid import UUID


from ...common.utils import json
from ..utils import cozo_query


@cozo_query
@beartype
def list_sessions_query(
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    metadata_filter: dict[str, Any] = {},
) -> tuple[str, dict]:
    """Lists sessions from the 'cozodb' database based on the provided filters.

    Parameters:
        developer_id (UUID): The developer's ID to filter sessions by.
        limit (int): The maximum number of sessions to return.
        offset (int): The offset from which to start listing sessions.
        metadata_filter (dict[str, Any]): A dictionary of metadata fields to filter sessions by.

    Returns:
        pd.DataFrame: A DataFrame containing the queried session data.
    """
    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

    query = f"""
        input[developer_id] <- [[
            to_uuid($developer_id),
        ]]

        ?[
            agent_id,
            user_id,
            id,
            situation,
            summary,
            updated_at,
            created_at,
            metadata,
        ] :=
            input[developer_id],
            *sessions{{
                developer_id,
                session_id: id,
                situation,
                summary,
                created_at,
                updated_at: validity,
                metadata,
                @ "NOW"
            }},
            *session_lookup{{
                agent_id,
                user_id,
                session_id: id,
            }},
            updated_at = to_int(validity),
            {metadata_filter_str}

        :limit $limit
        :offset $offset
        :sort -created_at
    """

    # Execute the datalog query and return the results as a pandas DataFrame.
    return (
        query,
        {"developer_id": str(developer_id), "limit": limit, "offset": offset},
    )
