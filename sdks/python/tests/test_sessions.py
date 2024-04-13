from ward import test


from julep.api.types import (
    Session,
    InputChatMlMessage,
    InputChatMlMessageRole,
    ChatResponse,
)

from .fixtures import (
    async_client,
    client,
    test_session,
    mock_session,
    mock_session_update,
    setup_agent_async,
    setup_user_async,
    setup_session_async,
)


@test("sessions.create")
def _(client=client, session=test_session):
    assert isinstance(session, Session)
    assert hasattr(session, "created_at")
    assert session.situation == mock_session["situation"]


@test("async sessions.create, sessions.get, sessions.update & sessions.delete")
async def _(client=async_client):
    agent = await setup_agent_async(client)
    user = await setup_user_async(client)
    session = await setup_session_async(client, user, agent)

    assert isinstance(session, Session)
    assert hasattr(session, "created_at")
    assert session.situation == mock_session["situation"]

    try:
        response = await client.sessions.get(id=session.id)
        assert isinstance(response, Session)
        assert response.id == session.id
        assert response.situation == session.situation

        # updated = await client.sessions.update(
        #     session_id=session.id,
        #     **mock_session_update,
        # )

        # assert updated.situation == mock_session_update["situation"]

    finally:
        response = await client.sessions.delete(session_id=session.id)
        assert response is None
        await client.agents.delete(agent_id=agent.id)
        await client.users.delete(user_id=user.id)


@test("sessions.get")
def _(client=client, session=test_session):
    response = client.sessions.get(id=session.id)

    assert isinstance(response, Session)
    assert response.id == session.id
    assert response.situation == session.situation


@test("sessions.list")
def _(client=client):
    response = client.sessions.list()
    assert len(response) > 0
    assert isinstance(response[0], Session)


@test("async sessions.list")
async def _(client=async_client):
    response = await client.sessions.list()
    assert len(response) > 0
    assert isinstance(response[0], Session)


@test("sessions.update")
def _(client=client, session=test_session):
    response = client.sessions.update(
        session_id=session.id,
        **mock_session_update,
    )

    assert isinstance(response, Session)
    assert response.updated_at
    assert response.situation == mock_session_update["situation"]


@test("sessions.update with overwrite")
def _(client=client, session=test_session):
    response = client.sessions.update(
        session_id=session.id,
        overwrite=True,
        **mock_session_update,
    )

    assert isinstance(response, Session)
    assert response.updated_at
    assert response.situation == mock_session_update["situation"]


@test("sessions.chat")
def _(client=client, session=test_session):
    response = client.sessions.chat(
        session_id=session.id,
        messages=[
            InputChatMlMessage(
                role=InputChatMlMessageRole.USER,
                content="test content",
                name="tets name",
            )
        ],
        # tools=[
        #     Tool(
        #         **{
        #             "type": "function",
        #             "function": {
        #                 "description": "test description",
        #                 "name": "test name",
        #                 "parameters": {"test_arg": "test val"},
        #             },
        #             "id": str(uuid4()),
        #         },
        #     )
        # ],
        # logit_bias={"test": 1},
        max_tokens=120,
        presence_penalty=0.5,
        repetition_penalty=0.5,
        seed=1,
        stream=False,
        temperature=0.7,
        top_p=0.9,
        recall=False,
        remember=False,
    )

    assert isinstance(response, ChatResponse)


# @test("sessions.suggestions")
# def _(client=client, session=test_session):
#     response = client.sessions.suggestions(
#         session_id=session.id,
#     )
#     assert len(response) > 0
#     assert isinstance(response[0], Suggestion)


# @test("async sessions.suggestions")
# async def _(client=async_client, session=test_session_async):
#     response = await client.sessions.suggestions(
#         session_id=session.id,
#     )
#     assert len(response) > 0
#     assert isinstance(response[0], Suggestion)


# @test("sessions.history")
# def _(client=client, session=test_session):
#     response = client.sessions.history(
#         session_id=session.id,
#     )
#     assert len(response) > 0
#     assert isinstance(response[0], ChatMlMessage)


# @test("async sessions.list")
# async def _(client=async_client, session=test_session_async):
#     response = await client.sessions.history(
#         session_id=session.id,
#     )
#     assert len(response) > 0
#     assert isinstance(response[0], ChatMlMessage)


@test("sessions.delete")
def _(client=client, session=test_session):
    response = client.sessions.delete(
        session_id=session.id,
    )

    assert response is None
