from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import (
    ResourceUpdatedResponse,
    UpdateToolRequest,
)
from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)


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
    _kind="replaced",
)
@cozo_query
@beartype
def update_tool(
    *,
    developer_id: UUID,
    agent_id: UUID,
    tool_id: UUID,
    data: UpdateToolRequest,
    **kwargs,
) -> tuple[list[str], dict]:
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    # Extract the tool data from the payload
    update_data = data.model_dump(exclude_none=True)

    # Assert that only one of the tool type fields is present
    tool_specs = [
        (tool_type, update_data.get(tool_type))
        for tool_type in ["function", "integration", "system", "api_call"]
        if update_data.get(tool_type) is not None
    ]

    assert len(tool_specs) <= 1, "Invalid tool update"
    tool_type, tool_spec = tool_specs[0] if tool_specs else (None, None)

    if tool_type is not None:
        update_data["type"] = update_data.get("type", tool_type)
        assert update_data["type"] == tool_type, "Invalid tool update"

    update_data["spec"] = tool_spec
    del update_data[tool_type]

    tool_cols, tool_vals = cozo_process_mutate_data(
        {
            **update_data,
            "agent_id": agent_id,
            "tool_id": tool_id,
        }
    )

    # Construct the datalog query for updating the tool information
    patch_query = f"""
        input[{tool_cols}] <- $input

        ?[{tool_cols}, created_at, updated_at] := 
            *tools {{
                agent_id: to_uuid($agent_id),
                tool_id: to_uuid($tool_id),
                created_at
            }},
            input[{tool_cols}],
            updated_at = now()

        :put tools {{ {tool_cols}, created_at, updated_at }}
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
