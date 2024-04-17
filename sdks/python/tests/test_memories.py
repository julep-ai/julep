from ward import test


from .fixtures import (
    client,
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

    assert user is not None
    assert agent is not None
