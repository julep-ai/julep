from uuid import UUID, uuid4

import pandas as pd

from ...autogen.openapi_model import FunctionDef
from ...clients.cozo import client


def create_tools_query(
    agent_id: UUID,
    functions: list[FunctionDef],
    embeddings: list[list[float]],
) -> pd.DataFrame:
    assert len(functions) == len(embeddings)

    functions_input: list[list] = []

    for function, embedding in zip(functions, embeddings):
        parameters = function.parameters.model_dump_json()
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

    return client.run(query, {"records": functions_input})
