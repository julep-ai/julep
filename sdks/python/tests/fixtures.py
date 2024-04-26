from typing import Optional

from environs import Env
from ward import fixture

from julep import AsyncClient, Client

from julep.api.types import Agent, User, Session

env = Env()

TEST_API_KEY: Optional[str] = env.str("TEST_API_KEY", "thisisnotarealapikey")
TEST_API_URL: Optional[str] = env.str("TEST_API_URL", "http://localhost:8080/api")
TEST_MODEL: Optional[str] = env.str("TEST_MODEL", "julep-ai/samantha-1-turbo")


mock_agent = {
    "name": "test agent",
    "about": "test agent about",
    "model": TEST_MODEL,
    "instructions": "test agent instructions",
    "default_settings": {"temperature": 0.5},
    "metadata": {"test": "test"},
}

mock_agent_update = {
    "name": "updated agent",
    "about": "updated agent about",
    "instructions": [
        "updated agent instructions",
    ],
    "metadata": {"test": "test"},
}

mock_user = {
    "name": "test user",
    "about": "test user about",
    "metadata": {"type": "test"},
}

mock_user_update = {
    "name": "updated user",
    "about": "updated user about",
    "metadata": {"type": "test"},
}

mock_session = {
    "situation": "test situation",
    "metadata": {"type": "test"},
}

mock_session_update = {
    "situation": "updated situation",
    "metadata": {"type": "test"},
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
    "metadata": {"type": "test"},
}


def cleanup(client: Client):
    for session in client.sessions.list(metadata_filter={"type": "test"}):
        client.sessions.delete(session.id)

    for agent in client.agents.list(metadata_filter={"test": "test"}):
        client.agents.delete(agent.id)

        for tool in client.tools.list(agent_id=agent.id):
            client.tools.delete(tool.id)

        for doc in client.docs.list(agent_id=agent.id):
            client.docs.delete(doc_id=doc.id, agent_id=agent.id)

    for user in client.users.list(metadata_filter={"type": "test"}):
        client.users.delete(user.id)

        for doc in client.docs.list(user_id=user.id):
            client.docs.delete(doc_id=doc.id, user_id=user.id)


@fixture(scope="global")
def client():
    client = Client(
        api_key=TEST_API_KEY,
        base_url=TEST_API_URL,
    )

    yield client

    cleanup(client)


@fixture
def async_client(_=client):
    client = AsyncClient(
        api_key=TEST_API_KEY,
        base_url=TEST_API_URL,
    )

    return client


@fixture
def test_agent(client=client) -> Agent:
    agent = client.agents.create(
        **mock_agent,
    )

    yield agent

    client.agents.delete(agent.id)


@fixture
async def test_agent_async(async_client=async_client, client=client) -> Agent:
    agent = await async_client.agents.create(
        **mock_agent,
    )

    yield agent

    client.agents.delete(agent.id)


@fixture
def test_user(client=client) -> User:
    user = client.users.create(
        **mock_user,
    )

    yield user

    client.users.delete(user.id)


@fixture
async def test_user_async(async_client=async_client, client=client) -> User:
    user = await async_client.users.create(
        **mock_user,
    )

    yield user

    client.users.delete(user.id)


@fixture
def test_session(client=client, user=test_user, agent=test_agent) -> Session:
    session = client.sessions.create(
        user_id=user.id,
        agent_id=agent.id,
        **mock_session,
    )

    yield session

    client.sessions.delete(session.id)


@fixture
def test_session_agent_user(client=client, user=test_user, agent=test_agent) -> Session:
    session = client.sessions.create(
        user_id=user.id,
        agent_id=agent.id,
        **mock_session,
    )

    yield session, agent, user

    client.sessions.delete(session.id)


@fixture
def test_session_no_user(client=client, agent=test_agent) -> Session:
    session = client.sessions.create(
        agent_id=agent.id,
        **mock_session,
    )

    yield session

    client.sessions.delete(session.id)


@fixture
async def test_session_async(
    client=async_client, user=test_user, agent=test_agent
) -> Session:
    session = await client.sessions.create(
        user_id=user.id,
        agent_id=agent.id,
        **mock_session,
    )

    yield session

    await client.sessions.delete(session.id)


@fixture
def test_tool(client=client, agent=test_agent):
    tool = client.tools.create(
        agent_id=agent.id,
        **mock_tool,
    )

    yield tool, agent

    client.tools.delete(agent_id=agent.id, tool_id=tool.id)


@fixture
def test_agent_doc(client=client, agent=test_agent):
    doc = client.docs.create(
        agent_id=agent.id,
        doc={**mock_doc},
    )

    yield doc, agent

    client.docs.delete(doc_id=doc.id, agent_id=agent.id)


@fixture
def test_user_doc(client=client, user=test_user):
    doc = client.docs.create(
        user_id=user.id,
        doc={**mock_doc},
    )

    yield doc, user

    client.docs.delete(doc_id=doc.id, user_id=user.id)
