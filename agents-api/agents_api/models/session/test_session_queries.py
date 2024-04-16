"""
This module contains tests for session-related queries against the 'cozodb' database. It verifies the creation, retrieval, and deletion of session records as defined in the schema provided in agents-api/README.md.
"""

# Tests for session queries
from uuid import uuid4

from cozo_migrate.api import init, apply
from pycozo import Client
from ward import test, skip

from ..agent.create_agent import create_agent_query
from ..user.create_user import create_user_query

from .create_session import create_session_query
from .delete_session import delete_session_query
from .get_session import get_session_query
from .list_sessions import list_sessions_query
from .session_data import get_session_data, session_data_query


MODEL = "julep-ai/samantha-1-turbo"


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("model: create session")
def _():
    """Test session creation with a valid session, user, agent, and developer IDs."""
    client = cozo_client()
    session_id = uuid4()
    agent_id = uuid4()
    user_id = uuid4()
    developer_id = uuid4()

    create_session_query(
        session_id=session_id,
        user_id=user_id,
        developer_id=developer_id,
        agent_id=agent_id,
        situation="test session about",
        client=client,
    )


@test("model: create session no user")
def _():
    """Test session creation without a user ID."""
    client = cozo_client()
    session_id = uuid4()
    agent_id = uuid4()
    developer_id = uuid4()

    create_session_query(
        session_id=session_id,
        user_id=None,
        developer_id=developer_id,
        agent_id=agent_id,
        situation="test session about",
        client=client,
    )


@test("model: get session not exists")
def _():
    """Verify that querying a non-existent session returns an empty result."""
    client = cozo_client()
    session_id = uuid4()
    developer_id = uuid4()

    result = get_session_query(
        session_id=session_id,
        developer_id=developer_id,
        client=client,
    )

    assert len(result["id"]) == 0


@test("model: get session exists")
def _():
    """Verify that a created session can be successfully retrieved."""
    client = cozo_client()
    session_id = uuid4()
    agent_id = uuid4()
    user_id = uuid4()
    developer_id = uuid4()

    result = create_session_query(
        session_id=session_id,
        user_id=user_id,
        agent_id=agent_id,
        developer_id=developer_id,
        situation="test session about",
        client=client,
    )

    result = get_session_query(
        session_id=session_id,
        developer_id=developer_id,
        client=client,
    )

    assert len(result["id"]) == 1


@test("model: get session data")
def _():
    """Test retrieval of session data for an existing session."""
    # Setup client for user and agent
    client = cozo_client()

    session_id = uuid4()
    agent_id = uuid4()
    user_id = uuid4()
    developer_id = uuid4()

    # Create a user
    create_user_query(
        user_id=user_id,
        developer_id=developer_id,
        about="test user about",
        name="test user name",
        client=client,
    )

    # Create an agent
    create_agent_query(
        agent_id=agent_id,
        model=MODEL,
        developer_id=developer_id,
        about="test agent about",
        name="test agent name",
        client=client,
    )

    # Create a session

    result = create_session_query(
        session_id=session_id,
        user_id=user_id,
        agent_id=agent_id,
        developer_id=developer_id,
        situation="test session about",
        client=client,
    )

    result = session_data_query(
        session_id=session_id,
        developer_id=developer_id,
        client=client,
    )

    assert len(result["user_about"]) == 1


@test("model: delete session")
def _():
    """Test the deletion of a session and verify it cannot be retrieved afterwards."""
    # Setup client for user and agent
    client = cozo_client()

    session_id = uuid4()
    agent_id = uuid4()
    user_id = uuid4()
    developer_id = uuid4()

    # Create a user
    create_user_query(
        user_id=user_id,
        developer_id=developer_id,
        about="test user about",
        name="test user name",
        client=client,
    )

    # Create an agent
    create_agent_query(
        agent_id=agent_id,
        model=MODEL,
        developer_id=developer_id,
        about="test agent about",
        name="test agent name",
        client=client,
    )

    # Create a session
    result = create_session_query(
        session_id=session_id,
        user_id=user_id,
        agent_id=agent_id,
        developer_id=developer_id,
        situation="test session about",
        client=client,
    )

    # Delete the session
    result = delete_session_query(
        session_id=session_id,
        developer_id=developer_id,
        client=client,
    )

    # Check that the session is deleted
    result = get_session_query(
        session_id=session_id,
        developer_id=developer_id,
        client=client,
    )

    assert len(result["id"]) == 0


@skip("get session data using get_session_data")
def _():
    # Setup client for user and agent
    client = cozo_client()

    developer_id = uuid4()
    session_id = uuid4()
    agent_id = uuid4()
    user_id = uuid4()

    # Setup: Create a user, agent, and session for testing session data retrieval using get_session_data.
    # Create a user
    create_user_query(
        user_id=user_id,
        developer_id=developer_id,
        about="test user about",
        name="test user name",
        client=client,
    )

    # Create an agent
    create_agent_query(
        developer_id=developer_id,
        model=MODEL,
        agent_id=agent_id,
        about="test agent about",
        name="test agent name",
        client=client,
    )

    # Create a session

    create_session_query(
        developer_id=developer_id,
        session_id=session_id,
        user_id=user_id,
        agent_id=agent_id,
        situation="test session about",
        client=client,
    )

    session_data = get_session_data(
        developer_id=developer_id,
        session_id=session_id,
        client=client,
    )

    assert session_data is not None
    assert session_data.user_about == "test user about"


@skip("list sessions")
def _():
    client = cozo_client()
    developer_id = uuid4()

    result = list_sessions_query(
        developer_id=developer_id,
        client=client,
    )

    assert len(result["id"]) == 0
