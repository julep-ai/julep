from uuid import UUID


from beartype import beartype

from ...autogen.openapi_model import PatchToolRequest, ResourceUpdatedResponse

from ..utils import cozo_query, verify_developer_id_query, wrap_in_class


@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["agent_id"], "jobs": [], **d},
)
@cozo_query
@beartype
def patch_tool_by_id_query(
    *, developer_id: UUID, tool_id: UUID, update_tool: PatchToolRequest
) -> tuple[str, dict]:
    """
    # Execute the datalog query and return the results as a DataFrame
    Updates the tool information for a given agent and tool ID in the 'cozodb' database.

    Parameters:
    - developer_id (UUID): The unique identifier of the developer.
    - tool_id (UUID): The unique identifier of the tool to be updated.
    - update_tool (PatchToolRequest): The request payload containing the updated tool information.

    Returns:
    - ResourceUpdatedResponse: The updated tool data.
    """
    # Agent update query
    # Convert the function definition to a dictionary for easier manipulation
    function = function.model_dump()
    # Prepare the parameters for the datalog query
    params = {
        "input": [
            [
                str(agent_id),
                str(tool_id),
                function["name"],
                function["description"],
                function.get("parameters", {}),
                embedding,
            ]
        ]
    }

    # Construct the datalog query for updating the tool information
    query = """
        input[agent_id, tool_id, name, description, parameters, embedding] <- $input

        ?[agent_id, tool_id, name, description, parameters, embedding, updated_at] := 
            input[agent_id, tool_id, name, description, parameters, embedding],
            updated_at = now()

        :update agent_functions {
            agent_id,
            tool_id,
            name,
            description,
            parameters,
            embedding,
            updated_at,
        }
        :returning
    """

    return (query, params)
