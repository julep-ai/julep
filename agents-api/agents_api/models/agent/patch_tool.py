from uuid import UUID


from ...autogen.openapi_model import FunctionDef

from ..utils import cozo_query


@cozo_query
def patch_tool_by_id_query(
    agent_id: UUID, tool_id: UUID, function: FunctionDef, embedding: list[float]
) -> tuple[str, dict]:
    """
    # Execute the datalog query and return the results as a DataFrame
    Updates the tool information for a given agent and tool ID in the 'cozodb' database.

    Parameters:
    - agent_id (UUID): The unique identifier of the agent.
    - tool_id (UUID): The unique identifier of the tool to be updated.
    - function (FunctionDef): The function definition containing the new tool information.
    - embedding (list[float]): The embedding vector associated with the tool.

    Returns:
    - pd.DataFrame: A DataFrame containing the result of the update operation.
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
