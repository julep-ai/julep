from uuid import UUID

from ...common.utils.datetime import utcnow
from ...autogen.openapi_model import FunctionDef
from ...common.protocol.functions import ParametersDict


def update_tool_by_id_query(
    agent_id: UUID, tool_id: UUID, function: FunctionDef, embedding: list[list[float]]
) -> str:
    # Agent update query
    agent_id = str(agent_id)
    tool_id = str(tool_id)
    function = function.model_dump()

    name = function["name"]
    description = function["description"]
    parameters = ParametersDict(**function["parameters"]).model_dump(exclude_none=True)

    return f"""
        input[agent_id, tool_id] <- [[to_uuid("{agent_id}"), to_uuid("{tool_id}")]]
        
        ?[name, description, parameters, embedding, updated_at] <- [
            ["{name}", "{description}", {parameters}, vec({embedding}), {utcnow()}]
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
