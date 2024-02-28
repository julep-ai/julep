from uuid import UUID, uuid4

from agents_api.autogen.openapi_model import FunctionDef


def create_tools_query(
    agent_id: UUID,
    functions: list[FunctionDef],
    embeddings: list[list[float]],
) -> str:
    assert len(functions) == len(embeddings)

    agent_id = str(agent_id)
    functions_input = []

    for function, embedding in zip(functions, embeddings):
        tool_id = uuid4()
        parameters = function.parameters.model_dump_json()
        functions_input.append(
            f"""[to_uuid("{agent_id}"), to_uuid("{tool_id}"), "{function.name}", "{function.description}", {parameters}, vec({embedding}), now()]"""
        )

    records = "\n".join(functions_input)

    return f"""
        ?[agent_id, tool_id, name, description, parameters, embedding, updated_at] <- [
            {records}
        ]

        :insert agent_functions {{
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
