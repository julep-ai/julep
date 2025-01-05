# """
# This module contains tests for SQL query generation functions in the sessions module.
# Tests verify the SQL queries without actually executing them against a database.
# """

from agents_api.autogen.openapi_model import (
    CreateOrUpdateSessionRequest,
    CreateSessionRequest,
    PatchSessionRequest,
    ResourceCreatedResponse,
    ResourceDeletedResponse,
    ResourceUpdatedResponse,
    Session,
    UpdateSessionRequest,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.sessions import (
    count_sessions,
    create_or_update_session,
    create_session,
    delete_session,
    get_session,
    list_sessions,
    patch_session,
    update_session,
)
from uuid_extensions import uuid7
from ward import raises, test

from tests.fixtures import (
    pg_dsn,
    test_agent,
    test_developer_id,
    test_session,
    test_user,
)


@test("query: create session sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, user=test_user):
    """Test that a session can be successfully created."""

    pool = await create_db_pool(dsn=dsn)
    session_id = uuid7()
    data = CreateSessionRequest(
        users=[user.id],
        agents=[agent.id],
        system_template="test system template",
    )
    result = await create_session(
        developer_id=developer_id,
        session_id=session_id,
        data=data,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, ResourceCreatedResponse), f"Result is not a Session, {result}"
    assert result.id == session_id


@test("query: create or update session sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, user=test_user):
    """Test that a session can be successfully created or updated."""

    pool = await create_db_pool(dsn=dsn)
    session_id = uuid7()
    data = CreateOrUpdateSessionRequest(
        users=[user.id],
        agents=[agent.id],
        system_template="test system template",
    )
    result = await create_or_update_session(
        developer_id=developer_id,
        session_id=session_id,
        data=data,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, ResourceUpdatedResponse)
    assert result.id == session_id
    assert result.updated_at is not None


@test("query: get session exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """Test retrieving an existing session."""

    pool = await create_db_pool(dsn=dsn)
    result = await get_session(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, Session)
    assert result.id == session.id


@test("query: get session does not exist")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test retrieving a non-existent session."""

    session_id = uuid7()
    pool = await create_db_pool(dsn=dsn)
    with raises(Exception):
        await get_session(
            session_id=session_id,
            developer_id=developer_id,
            connection_pool=pool,
        )


@test("query: list sessions")
async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """Test listing sessions with default pagination."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_sessions(
        developer_id=developer_id,
        limit=10,
        offset=0,
        connection_pool=pool,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert any(s.id == session.id for s in result)


@test("query: list sessions with filters")
async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """Test listing sessions with specific filters."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_sessions(
        developer_id=developer_id,
        limit=10,
        offset=0,
        connection_pool=pool,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(isinstance(s, Session) for s in result), (
        f"Result is not a list of sessions, {result}"
    )


@test("query: count sessions")
async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """Test counting the number of sessions for a developer."""

    pool = await create_db_pool(dsn=dsn)
    count = await count_sessions(
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert isinstance(count, dict)
    assert count["count"] >= 1


@test("query: update session sql")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    session=test_session,
    agent=test_agent,
    user=test_user,
):
    """Test that an existing session's information can be successfully updated."""

    pool = await create_db_pool(dsn=dsn)
    data = UpdateSessionRequest(
        token_budget=1000,
        forward_tool_calls=True,
        system_template="updated system template",
    )
    result = await update_session(
        session_id=session.id,
        developer_id=developer_id,
        data=data,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, ResourceUpdatedResponse)
    assert result.updated_at > session.created_at

    updated_session = await get_session(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )
    assert updated_session.forward_tool_calls is True


@test("query: patch session sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session, agent=test_agent):
    """Test that a session can be successfully patched."""

    pool = await create_db_pool(dsn=dsn)
    data = PatchSessionRequest(
        metadata={"test": "metadata"},
    )
    result = await patch_session(
        developer_id=developer_id,
        session_id=session.id,
        data=data,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, ResourceUpdatedResponse)
    assert result.updated_at > session.created_at

    patched_session = await get_session(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )
    assert patched_session.metadata == {"test": "metadata"}


@test("query: delete session sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """Test that a session can be successfully deleted."""

    pool = await create_db_pool(dsn=dsn)
    delete_result = await delete_session(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )

    assert delete_result is not None
    assert isinstance(delete_result, ResourceDeletedResponse)

    with raises(Exception):
        await get_session(
            developer_id=developer_id,
            session_id=session.id,
            connection_pool=pool,
        )
