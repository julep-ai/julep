from typing import Any, Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import Agent
from ...common.utils import json
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    wrap_in_class,
)


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(Agent)
@cozo_query
@beartype
def list_agents(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
) -> tuple[list[str], dict]:
    """
    Constructs and executes a datalog query to list agents from the 'cozodb' database.

    Parameters:
        developer_id: UUID of the developer.
        limit: Maximum number of agents to return.
        offset: Number of agents to skip before starting to collect the result set.
        metadata_filter: Dictionary to filter agents based on metadata.
        client: Instance of CozoClient to execute the query.
    """
    # Transforms the metadata_filter dictionary into a string representation for the datalog query.
    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

    sort = f"{'-' if direction == 'desc' else ''}{sort_by}"

    # Datalog query to retrieve agent information based on filters, sorted by creation date in descending order.
    queries = [
        verify_developer_id_query(developer_id),
        f"""
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
        :sort {sort}
        """,
    ]

    return (
        queries,
        {"developer_id": str(developer_id), "limit": limit, "offset": offset},
    )
