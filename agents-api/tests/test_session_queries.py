# """
# This module contains tests for SQL query generation functions in the sessions module.
# Tests verify the SQL queries without actually executing them against a database.
# """

from agents_api.autogen.openapi_model import (
    CreateOrUpdateSessionRequest,
    CreateSessionRequest,
    PatchSessionRequest,
    ResourceDeletedResponse,
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
import pytest

from tests.fixtures import (
    pg_dsn,
    test_agent,
    test_developer_id,
    test_session,
    test_user,
)


@pytest.mark.asyncio
async def test_query_create_session_sql(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, user=test_user):
    """query: create session sql"""
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
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, Session), f"Result is not a Session, {result}"
    assert result.id == session_id


@pytest.mark.asyncio
async def test_query_create_or_update_session_sql(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, user=test_user):
    """query: create or update session sql"""
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
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, Session)
    assert result.id == session_id
    assert result.updated_at is not None


@pytest.mark.asyncio
async def test_query_get_session_exists(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """query: get session exists"""
    """Test retrieving an existing session."""

    pool = await create_db_pool(dsn=dsn)
    result = await get_session(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, Session)
    assert result.id == session.id


@pytest.mark.asyncio
async def test_query_get_session_does_not_exist(dsn=pg_dsn, developer_id=test_developer_id):
    """query: get session does not exist"""
    """Test retrieving a non-existent session."""

    session_id = uuid7()
    pool = await create_db_pool(dsn=dsn)
    with pytest.raises(Exception):
        await get_session(
            session_id=session_id,
            developer_id=developer_id,
            connection_pool=pool,
        )  # type: ignore[not-callable]


@pytest.mark.asyncio
async def test_query_list_sessions(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """query: list sessions"""
    """Test listing sessions with default pagination."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_sessions(
        developer_id=developer_id,
        limit=10,
        offset=0,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert isinstance(result, list)
    assert len(result) >= 1
    assert any(s.id == session.id for s in result)


@pytest.mark.asyncio
async def test_query_list_sessions_with_filters(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """query: list sessions with filters"""
    """Test listing sessions with specific filters."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_sessions(
        developer_id=developer_id,
        limit=10,
        offset=0,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(isinstance(s, Session) for s in result), (
        f"Result is not a list of sessions, {result}"
    )


@pytest.mark.asyncio
async def test_query_count_sessions(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """query: count sessions"""
    """Test counting the number of sessions for a developer."""

    pool = await create_db_pool(dsn=dsn)
    count = await count_sessions(
        developer_id=developer_id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert isinstance(count, dict)
    assert count["count"] >= 1


@pytest.mark.asyncio
async def test_query_update_session_sql(
    """query: update session sql"""
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
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, Session)
    assert result.updated_at > session.created_at

    updated_session = await get_session(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]
    assert updated_session.forward_tool_calls is True


@pytest.mark.asyncio
async def test_query_patch_session_sql(dsn=pg_dsn, developer_id=test_developer_id, session=test_session, agent=test_agent):
    """query: patch session sql"""
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
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, Session)
    assert result.updated_at > session.created_at

    patched_session = await get_session(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]
    assert patched_session.metadata == {"test": "metadata"}


@pytest.mark.asyncio
async def test_query_delete_session_sql(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """query: delete session sql"""
    """Test that a session can be successfully deleted."""

    pool = await create_db_pool(dsn=dsn)
    delete_result = await delete_session(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert delete_result is not None
    assert isinstance(delete_result, ResourceDeletedResponse)

    with pytest.raises(Exception):
        await get_session(
            developer_id=developer_id,
            session_id=session.id,
            connection_pool=pool,
        )  # type: ignore[not-callable]
