from typing import Any
from uuid import UUID


from ...common.utils import json
from ..utils import cozo_query


@cozo_query
def list_agents_query(
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    metadata_filter: dict[str, Any] = {},
) -> tuple[str, dict]:
    """
    Constructs and executes a datalog query to list agents from the 'cozodb' database.

    Parameters:
        developer_id: UUID of the developer.
        limit: Maximum number of agents to return.
        offset: Number of agents to skip before starting to collect the result set.
        metadata_filter: Dictionary to filter agents based on metadata.
        client: Instance of CozoClient to execute the query.

    Returns:
        A pandas DataFrame containing the query results.
    """
    # Transforms the metadata_filter dictionary into a string representation for the datalog query.
    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

    # Datalog query to retrieve agent information based on filters, sorted by creation date in descending order.
    query = f"""
    {{
        input[developer_id] <- [[to_uuid($developer_id)]]

        ?[
            id,
            model,
            name,
            about,
            created_at,
            updated_at,
            metadata,
            instructions,
        ] := input[developer_id],
            *agents {{
                developer_id,
                agent_id: id,
                model,
                name,
                about,
                created_at,
                updated_at,
                metadata,
                instructions,
            }},
            {metadata_filter_str}
        
        :limit $limit
        :offset $offset
        :sort -created_at
    }}"""

    return (
        query,
        {"developer_id": str(developer_id), "limit": limit, "offset": offset},
    )
