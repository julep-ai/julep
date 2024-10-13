from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import PatchToolRequest, ResourceUpdatedResponse
from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["tool_id"], "jobs": [], **d},
    _kind="inserted",
)
@cozo_query
@beartype
def patch_tool(
    *, developer_id: UUID, agent_id: UUID, tool_id: UUID, data: PatchToolRequest
) -> tuple[list[str], dict]:
    """
    Execute the datalog query and return the results as a DataFrame
    Updates the tool information for a given agent and tool ID in the 'cozodb' database.

    Parameters:
        agent_id (UUID): The unique identifier of the agent.
        tool_id (UUID): The unique identifier of the tool to be updated.
        data (PatchToolRequest): The request payload containing the updated tool information.

    Returns:
        ResourceUpdatedResponse: The updated tool data.
    """

    agent_id = str(agent_id)
    tool_id = str(tool_id)

    # Extract the tool data from the payload
    patch_data = data.model_dump(exclude_none=True)

    # Assert that only one of the tool type fields is present
    tool_specs = [
        (tool_type, patch_data.get(tool_type))
        for tool_type in ["function", "integration", "system", "api_call"]
        if patch_data.get(tool_type) is not None
    ]

    assert len(tool_specs) <= 1, "Invalid tool update"
    tool_type, tool_spec = tool_specs[0] if tool_specs else (None, None)

    if tool_type is not None:
        patch_data["type"] = patch_data.get("type", tool_type)
        assert patch_data["type"] == tool_type, "Invalid tool update"

    tool_spec = tool_spec or {}
    if tool_spec:
        del patch_data[tool_type]

    tool_cols, tool_vals = cozo_process_mutate_data(
        {
            **patch_data,
            "agent_id": agent_id,
            "tool_id": tool_id,
        }
    )

    # Construct the datalog query for updating the tool information
    patch_query = f"""
        input[{tool_cols}] <- $input

        ?[{tool_cols}, spec, updated_at] := 
            *tools {{
                agent_id: to_uuid($agent_id),
                tool_id: to_uuid($tool_id),
                spec: old_spec,
            }},
            input[{tool_cols}],
            spec = concat(old_spec, $spec),
            updated_at = now()

        :update tools {{ {tool_cols}, spec, updated_at }}
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        patch_query,
    ]

    return (
        queries,
        dict(input=tool_vals, spec=tool_spec, agent_id=agent_id, tool_id=tool_id),
    )
