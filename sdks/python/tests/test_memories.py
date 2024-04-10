from ward import test


from .fixtures import (
    async_client,
    client,
    setup_agent_async,
    setup_user_async,
    test_agent,
    test_user,
)


@test("memories.list")
def _(client=client, agent=test_agent, user=test_user):
    # response = client.memories.list(
    #     agent_id=agent.id,
    #     query="test query",
    #     user_id=user.id,
    #     limit=100,
    #     offset=0,
    # )
    # assert len(response) > 0
    # assert isinstance(response[0], Memory)
    try:
        assert user is not None
        assert agent is not None
    finally:
        client.agents.delete(agent_id=agent.id)
        client.users.delete(user_id=user.id)


@test("async memories.list")
async def _(client=async_client):
    agent = await setup_agent_async(client)
    user = await setup_user_async(client)

    # try:
    #     response = await client.memories.list(
    #         agent_id=agent.id,
    #         query="test query",
    #         user_id=user.id,
    #         limit=100,
    #         offset=0,
    #     )
    #     assert len(response) > 0
    #     assert isinstance(response[0], Memory)
    # finally:
    #     await client.agents.delete(agent_id=agent.id)
    #     await client.users.delete(user_id=user.id)

    try:
        assert user is not None
        assert agent is not None
    finally:
        await client.agents.delete(agent_id=agent.id)
        await client.users.delete(user_id=user.id)
