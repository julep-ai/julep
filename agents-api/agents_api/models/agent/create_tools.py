"""This module contains functions for creating tools in the CozoDB database."""

from uuid import UUID, uuid4


from ...autogen.openapi_model import FunctionDef

from ..utils import cozo_query


@cozo_query
def create_tools_query(
    agent_id: UUID,
    functions: list[FunctionDef],
    embeddings: list[list[float]],
) -> tuple[str, dict]:
    """
    Constructs a datalog query for inserting tool records into the 'agent_functions' relation in the CozoDB.

    Parameters:
    - agent_id (UUID): The unique identifier for the agent.
    - functions (list[FunctionDef]): A list of function definitions to be inserted.
    - embeddings (list[list[float]]): A list of embeddings corresponding to each function.

    Returns:
    - pd.DataFrame: A DataFrame containing the results of the query execution.
    """
    # Ensure the number of functions matches the number of embeddings
    assert len(functions) == len(embeddings)

    # Construct the input records for the datalog query
    functions_input: list[list] = []

    for function, embedding in zip(functions, embeddings):
        parameters = function.parameters.model_dump()
        functions_input.append(
            [
                str(agent_id),
                str(uuid4()),
                function.name,
                function.description or "",
                parameters,
                embedding,
            ]
        )

    # Datalog query for inserting new tool records into the 'agent_functions' relation
    query = """
        input[agent_id, tool_id, name, description, parameters, embedding] <- $records
        ?[agent_id, tool_id, name, description, parameters, embedding, updated_at] :=
            input[agent_id, tool_id, name, description, parameters, embedding],
            updated_at = now(),

        :insert agent_functions {
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

    return (query, {"records": functions_input})
