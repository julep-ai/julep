from ward import test

from julep import AsyncClient
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
    test_session_with_template,
    test_session_agent_user,
    test_session_no_user,
    mock_session,
    mock_session_update,
    mock_session_with_template,
    TEST_API_KEY,
    TEST_API_URL,
)


@test("sessions: sessions.create")
def _(client=client, session=test_session):
    assert isinstance(session, Session)
    assert hasattr(session, "created_at")
    assert session.situation == mock_session["situation"]


@test(
    "sessions: async sessions.create, sessions.get, sessions.update & sessions.delete"
)
async def _(client=async_client, session_agent_user=test_session_agent_user):
    client = AsyncClient(
        api_key=TEST_API_KEY,
        base_url=TEST_API_URL,
    )
    session, agent, user = session_agent_user

    assert isinstance(session, Session)
    assert hasattr(session, "created_at")
    assert session.situation == mock_session["situation"]

    response = await client.sessions.get(id=session.id)
    assert isinstance(response, Session)
    assert response.id == session.id
    assert response.situation == session.situation

    updated = await client.sessions.update(
        session_id=session.id,
        **mock_session_update,
    )

    assert updated.situation == mock_session_update["situation"]


@test("sessions: sessions.create no user")
def _(client=client, session=test_session_no_user):
    assert isinstance(session, Session)
    assert session.id


@test("sessions: sessions.get no user")
def _(client=client, session=test_session_no_user):
    response = client.sessions.get(id=session.id)

    assert isinstance(response, Session)
    assert response.id == session.id


@test("sessions: sessions.get")
def _(client=client, session=test_session):
    response = client.sessions.get(id=session.id)

    assert isinstance(response, Session)
    assert response.id == session.id
    assert response.situation == session.situation


@test("sessions: sessions.list")
def _(client=client, session=test_session):
    response = client.sessions.list()
    assert len(response) > 0
    assert isinstance(response[0], Session)


@test("sessions: async sessions.list")
async def _(client=async_client, session=test_session):
    response = await client.sessions.list()
    assert len(response) > 0
    assert isinstance(response[0], Session)


@test("sessions: sessions.update")
def _(client=client, session=test_session):
    response = client.sessions.update(
        session_id=session.id,
        **mock_session_update,
    )

    assert isinstance(response, Session)
    assert response.updated_at
    assert response.situation == mock_session_update["situation"]


@test("sessions: sessions.update with overwrite")
def _(client=client, session=test_session):
    response = client.sessions.update(
        session_id=session.id,
        overwrite=True,
        **mock_session_update,
    )

    assert isinstance(response, Session)
    assert response.updated_at
    assert response.situation == mock_session_update["situation"]


@test("sessions: sessions.chat")
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
        max_tokens=120,
        presence_penalty=0.5,
        repetition_penalty=0.5,
        seed=1,
        stream=False,
        temperature=0.7,
        top_p=0.9,
        recall=True,
        remember=True,
    )

    assert isinstance(response, ChatResponse)

    history = client.sessions.history(
        session_id=session.id,
    )

    assert len(history) > 0


@test("sessions: sessions.chat with template")
def _(client=client, session=test_session_with_template):
    response = client.sessions.chat(
        session_id=session.id,
        messages=[
            InputChatMlMessage(
                role=InputChatMlMessageRole.USER,
                content="say it please",
            )
        ],
        max_tokens=10,
    )

    assert isinstance(response, ChatResponse)
    assert (
        mock_session_with_template["metadata"]["arg"] in response.response[0][0].content
    )


# @test("sessions: sessions.suggestions")
# def _(client=client, session=test_session):
#     response = client.sessions.suggestions(
#         session_id=session.id,
#     )
#     assert len(response) > 0
#     assert isinstance(response[0], Suggestion)


# @test("sessions: async sessions.suggestions")
# async def _(client=async_client, session=test_session_async):
#     response = await client.sessions.suggestions(
#         session_id=session.id,
#     )
#     assert len(response) > 0
#     assert isinstance(response[0], Suggestion)


@test("sessions: sessions.history empty")
def _(client=client, session=test_session):
    response = client.sessions.history(
        session_id=session.id,
    )

    assert len(response) == 0


@test("sessions: sessions.delete_history")
def _(client=client, session=test_session):
    response = client.sessions.delete_history(
        session_id=session.id,
    )

    assert response is None

    history = client.sessions.history(
        session_id=session.id,
    )

    assert len(history) == 0


@test("sessions: sessions.delete")
def _(client=client, session=test_session):
    response = client.sessions.delete(
        session_id=session.id,
    )

    assert response is None
