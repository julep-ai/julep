from uuid import UUID

import pandas as pd

from ...autogen.openapi_model import FunctionDef
from ...clients.cozo import client
from ...common.utils import json


def patch_tool_by_id_query(
    agent_id: UUID, tool_id: UUID, function: FunctionDef, embedding: list[float]
) -> pd.DataFrame:
    # Agent update query
    function = function.model_dump()

    name = json.dumps(function["name"])
    description = json.dumps(function["description"])
    parameters = json.dumps(function.get("parameters", {}))

    query = f"""
        ?[agent_id, tool_id, name, description, parameters, embedding, updated_at] <- [
            [to_uuid("{agent_id}"), to_uuid("{tool_id}"), {name}, {description}, {parameters}, vec({embedding}), now()]
        ]

        :update agent_functions {{
            agent_id,
            tool_id,
            name,
            description,
            parameters,
            embedding,
            updated_at,
        }}
        :returning
    """

    return client.run(query)
