from typing import Optional, Tuple

from environs import Env
from ward import fixture

from julep import AsyncClient, Client

from julep.api.types import Agent, User, Session, ResourceCreatedResponse

env = Env()

TEST_API_KEY: Optional[str] = env.str("TEST_API_KEY", "thisisnotarealapikey")
TEST_API_URL: Optional[str] = env.str("TEST_API_URL", "http://localhost:8080/api")


mock_agent = {
    "name": "test agent",
    "about": "test agent about",
    "instructions": [
        "test agent instructions",
    ],
    "default_settings": {"temperature": 0.5},
}

mock_agent_update = {
    "name": "updated agent",
    "about": "updated agent about",
    "instructions": [
        "updated agent instructions",
    ],
}

mock_user = {
    "name": "test user",
    "about": "test user about",
}

mock_user_update = {
    "name": "updated user",
    "about": "updated user about",
}

mock_session = {
    "situation": "test situation",
}

mock_session_update = {
    "situation": "updated situation",
}

mock_tool = {
    "tool": {
        "type": "function",
        "function": {
            "description": "test description",
            "name": "test name",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_arg": {"type": "string", "default": "test val"},
                },
            },
        },
    }
}

mock_tool_update = {
    "function": {
        "description": "updated description",
        "name": "updated name",
        "parameters": {
            "type": "object",
            "properties": {
                "test_arg": {"type": "string", "default": "test val"},
            },
        },
    },
}

mock_doc = {
    "title": "test title",
    "content": "test content",
}


@fixture(scope="global")
def client():
    client = Client(
        api_key=TEST_API_KEY,
        base_url=TEST_API_URL,
    )

    return client


@fixture
async def async_client():
    client = AsyncClient(
        api_key=TEST_API_KEY,
        base_url=TEST_API_URL,
    )

    return client


@fixture
def test_agent(client=client) -> Agent:
    response = client.agents.create(
        **mock_agent,
    )
    return response


@fixture
async def test_agent_async(client=async_client) -> Agent:
    response = await client.agents.create(
        **mock_agent,
    )
    return response


@fixture
def test_user(client=client) -> User:
    response = client.users.create(
        **mock_user,
    )
    return response


@fixture
async def test_user_async(client=async_client) -> User:
    response = await client.users.create(
        **mock_user,
    )
    return response


@fixture
def test_session(client=client, user=test_user, agent=test_agent) -> Session:
    response = client.sessions.create(
        user_id=user.id,
        agent_id=agent.id,
        **mock_session,
    )
    return response


@fixture
def test_session_no_user(client=client, agent=test_agent) -> Session:
    response = client.sessions.create(
        agent_id=agent.id,
        **mock_session,
    )
    return response


@fixture
async def test_session_async(
    client=async_client, user=test_user, agent=test_agent
) -> Session:
    response = await client.sessions.create(
        user_id=user.id,
        agent_id=agent.id,
        **mock_session,
    )
    return response


@fixture
def test_tool(client=client, agent=test_agent) -> Tuple[Agent, ResourceCreatedResponse]:
    response = client.tools.create(
        agent_id=agent.id,
        **mock_tool,
    )
    return agent, response


# @fixture
# def test_memory(client=client, agent=test_agent, user=test_user) -> Tuple[Agent, ResourceCreatedResponse]:

#     response = client.memory.create(
#         agent_id=agent.id,
#         **mock_tool,
#     )
#     return agent, response


@fixture
def test_agent_doc(
    client=client, agent=test_agent
) -> Tuple[Agent, ResourceCreatedResponse]:
    response = client.docs.create(
        agent_id=agent.id,
        doc={**mock_doc},
    )
    return agent, response


@fixture
def test_user_doc(
    client=client, user=test_user
) -> Tuple[User, ResourceCreatedResponse]:
    response = client.docs.create(
        user_id=user.id,
        doc={**mock_doc},
    )
    return user, response


async def setup_agent_async(client):
    agent = await client.agents.create(**mock_agent)
    return agent


async def setup_user_async(client):
    user = await client.users.create(**mock_user)
    return user


async def setup_session_async(client, user, agent):
    session = await client.sessions.create(
        user_id=user.id,
        agent_id=agent.id,
        **mock_session,
    )
    return session


async def setup_agent_doc_async(client, agent):
    doc = await client.docs.create(agent_id=agent.id, doc={**mock_doc})
    return doc


async def setup_user_doc_async(client, user):
    doc = await client.docs.create(user_id=user.id, doc={**mock_doc})
    return doc


async def setup_tool_async(client, agent):
    tool = await client.tools.create(agent_id=agent.id, **mock_tool)
    return tool
