from uuid import UUID

from beartype import beartype


from ..utils import cozo_query


@cozo_query
@beartype
def embed_functions_query(
    agent_id: UUID,
    tool_ids: list[UUID],
    embeddings: list[list[float]],
) -> tuple[str, dict]:
    agent_id = str(agent_id)
    tool_ids = [str(id) for id in tool_ids]
    assert len(tool_ids) == len(embeddings)

    records = [
        [agent_id, tool_id, embedding]
        for tool_id, embedding in zip(tool_ids, embeddings)
    ]

    query = """
    {
        ?[agent_id, tool_id, embedding] <- $records

        :update agent_functions {
            agent_id, tool_id, embedding
        }
        :returning
    }"""

    return (query, {"records": records})
