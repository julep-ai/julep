"""
This module contains tests for SQL query generation functions in the users module.
Tests verify the SQL queries without actually executing them against a database.
"""

from uuid import UUID

import asyncpg
from uuid_extensions import uuid7
from ward import raises, test

from agents_api.autogen.openapi_model import (
    CreateOrUpdateUserRequest,
    CreateUserRequest,
    PatchUserRequest,
    ResourceDeletedResponse,
    ResourceUpdatedResponse,
    UpdateUserRequest,
    User,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.users import (
    create_or_update_user,
    create_user,
    delete_user,
    get_user,
    list_users,
    patch_user,
    update_user,
)
from tests.fixtures import pg_dsn, test_developer_id, test_user

# Test UUIDs for consistent testing
TEST_DEVELOPER_ID = UUID("123e4567-e89b-12d3-a456-426614174000")
TEST_USER_ID = UUID("987e6543-e21b-12d3-a456-426614174000")


@test("query: create user sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that a user can be successfully created."""

    pool = await create_db_pool(dsn=dsn)
    await create_user(
        developer_id=developer_id,
        data=CreateUserRequest(
            name="test user",
            about="test user about",
        ),
        connection_pool=pool,
    )


@test("query: create or update user sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that a user can be successfully created or updated."""

    pool = await create_db_pool(dsn=dsn)
    await create_or_update_user(
        developer_id=developer_id,
        user_id=uuid7(),
        data=CreateOrUpdateUserRequest(
            name="test user",
            about="test user about",
        ),
        connection_pool=pool,
    )


@test("query: update user sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, user=test_user):
    """Test that an existing user's information can be successfully updated."""

    pool = await create_db_pool(dsn=dsn)
    update_result = await update_user(
        user_id=user.id,
        developer_id=developer_id,
        data=UpdateUserRequest(
            name="updated user",
            about="updated user about",
        ),
        connection_pool=pool,
    )

    assert update_result is not None
    assert isinstance(update_result, ResourceUpdatedResponse)
    assert update_result.updated_at > user.created_at


@test("query: get user not exists sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that retrieving a non-existent user returns an empty result."""

    user_id = uuid7()

    pool = await create_db_pool(dsn=dsn)

    with raises(Exception):
        await get_user(
            user_id=user_id,
            developer_id=developer_id,
            connection_pool=pool,
        )


@test("query: get user exists sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, user=test_user):
    """Test that retrieving an existing user returns the correct user information."""

    pool = await create_db_pool(dsn=dsn)
    result = await get_user(
        user_id=user.id,
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, User)


@test("query: list users sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing users returns a collection of user information."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_users(
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(isinstance(user, User) for user in result)


@test("query: patch user sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, user=test_user):
    """Test that a user can be successfully patched."""

    pool = await create_db_pool(dsn=dsn)
    patch_result = await patch_user(
        developer_id=developer_id,
        user_id=user.id,
        data=PatchUserRequest(
            name="patched user",
            about="patched user about",
            metadata={"test": "metadata"},
        ),
        connection_pool=pool,
    )

    assert patch_result is not None
    assert isinstance(patch_result, ResourceUpdatedResponse)
    assert patch_result.updated_at > user.created_at


@test("query: delete user sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, user=test_user):
    """Test that a user can be successfully deleted."""

    pool = await create_db_pool(dsn=dsn)
    delete_result = await delete_user(
        developer_id=developer_id,
        user_id=user.id,
        connection_pool=pool,
    )

    assert delete_result is not None
    assert isinstance(delete_result, ResourceDeletedResponse)

    # Verify the user no longer exists
    try:
        await get_user(
            developer_id=developer_id,
            user_id=user.id,
            connection_pool=pool,
        )
    except Exception:
        pass
    else:
        assert (
            False
        ), "Expected an exception to be raised when retrieving a deleted user."
