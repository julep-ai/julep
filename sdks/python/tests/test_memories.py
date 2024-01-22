from uuid import uuid4

from ward import test

# from julep_ai.api.types import (
#     Memory,
# )

from .fixtures import async_client, client


@test("memories.list")
def _(client=client):
    response = client.memories.list(
        agent_id=str(uuid4()),
        query="test query",
        types="test types",
        user_id=str(uuid4()),
        limit=100,
        offset=0,
    )
    assert len(response) > 0
    # assert isinstance(response[0], Memory)


@test("async memories.list")
async def _(client=async_client):
    response = await client.memories.list(
        agent_id=str(uuid4()),
        query="test query",
        types="test types",
        user_id=str(uuid4()),
        limit=100,
        offset=0,
    )
    assert len(response) > 0
    # assert isinstance(response[0], Memory)
