"""
This module contains tests for SQL query generation functions in the sessions module.
Tests verify the SQL queries without actually executing them against a database.
"""

from uuid import UUID

import asyncpg
from uuid_extensions import uuid7
from ward import raises, test

from agents_api.autogen.openapi_model import (
    CreateOrUpdateSessionRequest,
    CreateSessionRequest,
    PatchSessionRequest,
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
from tests.fixtures import (
    pg_dsn,
    test_developer_id,
)  # , test_session, test_agent, test_user

# @test("query: create session sql")
# async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, user=test_user):
#     """Test that a session can be successfully created."""

#     pool = await create_db_pool(dsn=dsn)
#     await create_session(
#         developer_id=developer_id,
#         session_id=uuid7(),
#         data=CreateSessionRequest(
#             users=[user.id],
#             agents=[agent.id],
#             situation="test session",
#         ),
#         connection_pool=pool,
#     )


# @test("query: create or update session sql")
# async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, user=test_user):
#     """Test that a session can be successfully created or updated."""

#     pool = await create_db_pool(dsn=dsn)
#     await create_or_update_session(
#         developer_id=developer_id,
#         session_id=uuid7(),
#         data=CreateOrUpdateSessionRequest(
#             users=[user.id],
#             agents=[agent.id],
#             situation="test session",
#         ),
#         connection_pool=pool,
#     )


# @test("query: update session sql")
# async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session, agent=test_agent):
#     """Test that an existing session's information can be successfully updated."""

#     pool = await create_db_pool(dsn=dsn)
#     update_result = await update_session(
#         session_id=session.id,
#         developer_id=developer_id,
#         data=UpdateSessionRequest(
#             agents=[agent.id],
#             situation="updated session",
#         ),
#         connection_pool=pool,
#     )

#     assert update_result is not None
#     assert isinstance(update_result, ResourceUpdatedResponse)
#     assert update_result.updated_at > session.created_at


@test("query: get session not exists sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that retrieving a non-existent session returns an empty result."""

    session_id = uuid7()
    pool = await create_db_pool(dsn=dsn)

    with raises(Exception):
        await get_session(
            session_id=session_id,
            developer_id=developer_id,
            connection_pool=pool,
        )


# @test("query: get session exists sql")
# async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
#     """Test that retrieving an existing session returns the correct session information."""

#     pool = await create_db_pool(dsn=dsn)
#     result = await get_session(
#         session_id=session.id,
#         developer_id=developer_id,
#         connection_pool=pool,
#     )

#     assert result is not None
#     assert isinstance(result, Session)


@test("query: list sessions sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing sessions returns a collection of session information."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_sessions(
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(isinstance(session, Session) for session in result)


# @test("query: patch session sql")
# async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session, agent=test_agent):
#     """Test that a session can be successfully patched."""

#     pool = await create_db_pool(dsn=dsn)
#     patch_result = await patch_session(
#         developer_id=developer_id,
#         session_id=session.id,
#         data=PatchSessionRequest(
#             agents=[agent.id],
#             situation="patched session",
#             metadata={"test": "metadata"},
#         ),
#         connection_pool=pool,
#     )

#     assert patch_result is not None
#     assert isinstance(patch_result, ResourceUpdatedResponse)
#     assert patch_result.updated_at > session.created_at


# @test("query: delete session sql")
# async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
#     """Test that a session can be successfully deleted."""

#     pool = await create_db_pool(dsn=dsn)
#     delete_result = await delete_session(
#         developer_id=developer_id,
#         session_id=session.id,
#         connection_pool=pool,
#     )

#     assert delete_result is not None
#     assert isinstance(delete_result, ResourceDeletedResponse)

#     # Verify the session no longer exists
#     with raises(Exception):
#         await get_session(
#             developer_id=developer_id,
#             session_id=session.id,
#             connection_pool=pool,
#         )


@test("query: count sessions sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that sessions can be counted."""

    pool = await create_db_pool(dsn=dsn)
    result = await count_sessions(
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert isinstance(result, dict)
    assert "count" in result
    assert isinstance(result["count"], int)
