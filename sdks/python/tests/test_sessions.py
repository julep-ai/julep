from uuid import uuid4

from ward import test

from julep.api.types import (
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    Session,
    ChatResponse,
    InputChatMlMessage,
    InputChatMlMessageRole,
    ChatMlMessage,
    ToolChoiceOption,
    ChatSettingsResponseFormat,
    ChatSettingsResponseFormatType,
    Tool,
    Suggestion,
)

from .fixtures import async_client, client


@test("sessions.get")
def _(client=client):
    response = client.sessions.get(id=uuid4())
    assert isinstance(response, Session)


@test("async sessions.get")
async def _(client=async_client):
    response = await client.sessions.get(id=uuid4())
    assert isinstance(response, Session)


@test("sessions.create")
def _(client=client):
    response = client.sessions.create(
        user_id=uuid4(),
        agent_id=uuid4(),
        situation="test situation",
    )

    assert isinstance(response, ResourceCreatedResponse)
    assert response.created_at


@test("async sessions.create")
async def _(client=async_client):
    response = await client.sessions.create(
        user_id=uuid4(),
        agent_id=uuid4(),
        situation="test situation",
    )

    assert isinstance(response, ResourceCreatedResponse)
    assert response.created_at


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
def _(client=client):
    response = client.sessions.update(
        session_id=uuid4(),
        situation="test situation",
    )

    assert isinstance(response, ResourceUpdatedResponse)
    assert response.updated_at


@test("async sessions.update")
async def _(client=async_client):
    response = await client.sessions.update(
        session_id=uuid4(),
        situation="test situation",
    )

    assert isinstance(response, ResourceUpdatedResponse)
    assert response.updated_at


@test("sessions.delete")
def _(client=client):
    response = client.sessions.delete(
        session_id=uuid4(),
    )

    assert response is None


@test("async sessions.delete")
async def _(client=async_client):
    response = await client.sessions.delete(
        session_id=uuid4(),
    )

    assert response is None


@test("sessions.chat")
def _(client=client):
    response = client.sessions.chat(
        session_id=str(uuid4()),
        messages=[
            InputChatMlMessage(
                role=InputChatMlMessageRole.USER,
                content="test content",
                name="tets name",
            )
        ],
        tools=[
            Tool(
                **{
                    "type": "function",
                    "function": {
                        "description": "test description",
                        "name": "test name",
                        "parameters": {"test_arg": "test val"},
                    },
                    "id": str(uuid4()),
                },
            )
        ],
        tool_choice=ToolChoiceOption("auto"),
        frequency_penalty=0.5,
        length_penalty=0.5,
        logit_bias={"test": 1},
        max_tokens=120,
        presence_penalty=0.5,
        repetition_penalty=0.5,
        response_format=ChatSettingsResponseFormat(
            type=ChatSettingsResponseFormatType.TEXT,
        ),
        seed=1,
        stop=["<"],
        stream=False,
        temperature=0.7,
        top_p=0.9,
        recall=False,
        remember=False,
    )

    assert isinstance(response, ChatResponse)


@test("async sessions.chat")
async def _(client=async_client):
    response = await client.sessions.chat(
        session_id=str(uuid4()),
        messages=[
            dict(
                role="user",
                content="test content",
                name="tets name",
            )
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "description": "test description",
                    "name": "test name",
                    "parameters": {"test_arg": "test val"},
                },
                "id": str(uuid4()),
            },
        ],
        tool_choice="auto",
        frequency_penalty=0.5,
        length_penalty=0.5,
        logit_bias={"test": 1},
        max_tokens=120,
        presence_penalty=0.5,
        repetition_penalty=0.5,
        response_format=dict(
            type="text",
        ),
        seed=1,
        stop=["<"],
        stream=False,
        temperature=0.7,
        top_p=0.9,
        recall=False,
        remember=False,
    )

    assert isinstance(response, ChatResponse)


@test("sessions.suggestions")
def _(client=client):
    response = client.sessions.suggestions(
        session_id=uuid4(),
    )
    assert len(response) > 0
    assert isinstance(response[0], Suggestion)


@test("async sessions.suggestions")
async def _(client=async_client):
    response = await client.sessions.suggestions(
        session_id=uuid4(),
    )
    assert len(response) > 0
    assert isinstance(response[0], Suggestion)


@test("sessions.history")
def _(client=client):
    response = client.sessions.history(
        session_id=uuid4(),
    )
    assert len(response) > 0
    assert isinstance(response[0], ChatMlMessage)


@test("async sessions.list")
async def _(client=async_client):
    response = await client.sessions.history(
        session_id=uuid4(),
    )
    assert len(response) > 0
    assert isinstance(response[0], ChatMlMessage)
