import litellm
from litellm import aembedding

from ..env import google_project_id, vertex_location

litellm.vertex_project = google_project_id
litellm.vertex_location = vertex_location


async def embed(
    inputs: list[str], dimensions: int = 1024, join_inputs: bool = True
) -> list[list[float]]:
    input = ["\n\n".join(inputs)] if join_inputs else inputs
    response = await aembedding(
        model="vertex_ai/text-embedding-004", input=input, dimensions=dimensions
    )

    return response.data or []
