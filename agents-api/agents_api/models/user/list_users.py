from typing import Any
from uuid import UUID

from beartype import beartype


from ..utils import cozo_query
from ...common.utils import json


@cozo_query
@beartype
def list_users_query(
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    metadata_filter: dict[str, Any] = {},
) -> tuple[str, dict]:
    """
    Queries the 'cozodb' database to list users associated with a specific developer.

    Parameters:
    - developer_id (UUID): The unique identifier of the developer.
    - limit (int): The maximum number of users to return. Defaults to 100.
    - offset (int): The number of users to skip before starting to collect the result set. Defaults to 0.
    - metadata_filter (dict[str, Any]): A dictionary representing filters to apply on user metadata.

    Returns:
    - pd.DataFrame: A DataFrame containing the queried user data.
    """
    # Construct a filter string for the metadata based on the provided dictionary.
    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

    # Define the datalog query for retrieving user information based on the specified filters and sorting them by creation date in descending order.
    query = f"""
    input[developer_id] <- [[to_uuid($developer_id)]]

    ?[
        id,
        name,
        about,
        created_at,
        updated_at,
        metadata,
    ] :=
        input[developer_id],
        *users {{
            user_id: id,
            developer_id,
            name,
            about,
            created_at,
            updated_at,
            metadata,
        }},
        {metadata_filter_str}

    :limit $limit
    :offset $offset
    :sort -created_at
    """

    # Execute the datalog query with the specified parameters and return the results as a DataFrame.
    return (
        query,
        {"developer_id": str(developer_id), "limit": limit, "offset": offset},
    )
