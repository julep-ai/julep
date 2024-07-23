from uuid import UUID


from beartype import beartype

from ...autogen.openapi_model import PatchToolRequest, ResourceUpdatedResponse
from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import cozo_query, verify_developer_id_query, wrap_in_class


@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["tool_id"], "jobs": [], **d},
)
@cozo_query
@beartype
def patch_tool_by_id_query(
    *, agent_id: UUID, tool_id: UUID, patch_tool: PatchToolRequest
) -> tuple[str, dict]:
    """
    # Execute the datalog query and return the results as a DataFrame
    Updates the tool information for a given agent and tool ID in the 'cozodb' database.

    Parameters:
    - agent_id (UUID): The unique identifier of the agent.
    - tool_id (UUID): The unique identifier of the tool to be updated.
    - patch_tool (PatchToolRequest): The request payload containing the updated tool information.

    Returns:
    - ResourceUpdatedResponse: The updated tool data.
    """


    # Extract the tool data from the payload
    patch_data = patch_tool.model_dump()

    # Assert that only one of the tool type fields is present
    if tool_type := patch_data.get("type"):
        assert patch_data[tool_type] is not None, f"Missing {tool_type} field"
    else:
        assert len([
            patch_data.get(tool_type) is not None for tool_type in ["function", "integration", "system", "api_call"]
        ]) == 1, "Invalid tool update"

        patch_data["type"] = next(
            tool_type for tool_type in ["function", "integration", "system", "api_call"]
            if patch_data.get(tool_type) is not None
        )

    # Rename the tool definition to 'spec'
    patch_data["spec"] = patch_data.pop(patch_data["type"])

    tool_cols, tool_vals = cozo_process_mutate_data(
        {
            **patch_data,
            "agent_id": str(agent_id),
            "tool_id": str(tool_id),
        }
    )

    # Construct the datalog query for updating the tool information
    query = f"""
        input[{tool_cols}] <- $input

        ?[{tool_cols}, updated_at] := 
            input[{tool_cols}],
            updated_at = now()

        :update tools {{ {tool_cols}, updated_at }}
        :returning
    """

    return (query, tool_vals)
