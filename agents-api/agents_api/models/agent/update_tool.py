from uuid import UUID

import pandas as pd

from ...autogen.openapi_model import FunctionDef
from ...clients.cozo import client


def update_tool_by_id_query(
    agent_id: UUID, tool_id: UUID, function: FunctionDef, embedding: list[float]
) -> pd.DataFrame:
    # Agent update query
    function = function.model_dump()
    params = {
        "input": [
            [
                str(agent_id),
                str(tool_id),
                function["name"],
                function.get("description", "") or "",
                function.get("parameters", {}) or {},
                embedding,
            ]
        ]
    }

    query = """
        input[agent_id, tool_id, name, description, parameters, embedding] <- $input
        ?[agent_id, tool_id, name, description, parameters, embedding, updated_at] :=
            input[agent_id, tool_id, name, description, parameters, embedding],
            updated_at= now()

        :put agent_functions {
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

    return client.run(query, params)
