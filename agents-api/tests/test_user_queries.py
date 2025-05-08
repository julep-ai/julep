"""
This module contains tests for SQL query generation functions in the users module.
Tests verify the SQL queries without actually executing them against a database.
"""

from uuid import UUID

from agents_api.app import app
from agents_api.autogen.openapi_model import (
    CreateOrUpdateUserRequest,
    CreateUserRequest,
    PatchUserRequest,
    ResourceDeletedResponse,
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
from fastapi.exceptions import HTTPException
from uuid_extensions import uuid7
from ward import raises, test

from tests.fixtures import pg_dsn, test_developer_id, test_project, test_user

# Test UUIDs for consistent testing
TEST_DEVELOPER_ID = UUID("123e4567-e89b-12d3-a456-426614174000")
TEST_USER_ID = UUID("987e6543-e21b-12d3-a456-426614174000")


@test("query: create user sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that a user can be successfully created."""

    pool = await create_db_pool(dsn=dsn)
    user = await create_user(
        developer_id=developer_id,
        data=CreateUserRequest(
            name="test user",
            about="test user about",
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    assert isinstance(user, User)
    assert user.id is not None
    assert user.name == "test user"
    assert user.about == "test user about"


@test("query: create user with project sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, project=test_project):
    """Test that a user can be successfully created with a project."""

    pool = await create_db_pool(dsn=dsn)
    user = await create_user(
        developer_id=developer_id,
        data=CreateUserRequest(
            name="test user with project",
            about="test user about",
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    assert isinstance(user, User)
    assert user.id is not None
    assert user.project == project.canonical_name


@test("query: create user with invalid project sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that creating a user with an invalid project raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with raises(HTTPException) as exc:
        await create_user(
            developer_id=developer_id,
            data=CreateUserRequest(
                name="test user with invalid project",
                about="test user about",
                project="invalid_project",
            ),
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.raised.status_code == 404
    assert "Project 'invalid_project' not found" in exc.raised.detail


@test("query: create or update user sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that a user can be successfully created or updated."""

    app.state.postgres_pool = pool = await create_db_pool(dsn=dsn)
    user = await create_or_update_user(
        developer_id=developer_id,
        user_id=uuid7(),
        data=CreateOrUpdateUserRequest(
            name="test user",
            about="test user about",
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    assert isinstance(user, User)
    assert user.id is not None
    assert user.name == "test user"
    assert user.about == "test user about"


@test("query: create or update user with project sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, project=test_project):
    """Test that a user can be successfully created or updated with a project."""

    app.state.postgres_pool = pool = await create_db_pool(dsn=dsn)
    user = await create_or_update_user(
        developer_id=developer_id,
        user_id=uuid7(),
        data=CreateOrUpdateUserRequest(
            name="test user with project",
            about="test user about",
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    assert isinstance(user, User)
    assert user.id is not None
    assert user.project == project.canonical_name


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
    )  # type: ignore[not-callable]

    assert update_result is not None
    assert isinstance(update_result, User)
    assert update_result.updated_at > user.created_at


@test("query: update user with project sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, user=test_user, project=test_project):
    """Test that an existing user's information can be successfully updated with a project."""

    pool = await create_db_pool(dsn=dsn)
    update_result = await update_user(
        user_id=user.id,
        developer_id=developer_id,
        data=UpdateUserRequest(
            name="updated user with project",
            about="updated user about",
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert update_result is not None
    assert isinstance(update_result, User)
    assert update_result.updated_at > user.created_at
    assert update_result.project == project.canonical_name


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
        )  # type: ignore[not-callable]


@test("query: get user exists sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, user=test_user):
    """Test that retrieving an existing user returns the correct user information."""

    pool = await create_db_pool(dsn=dsn)
    result = await get_user(
        user_id=user.id,
        developer_id=developer_id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, User)


@test("query: list users sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, user=test_user):
    """Test that listing users returns a collection of user information."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_users(
        developer_id=developer_id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(isinstance(user, User) for user in result)


@test("query: list users with project filter sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, project=test_project):
    """Test that listing users with a project filter returns the correct users."""

    pool = await create_db_pool(dsn=dsn)

    # First create a user with the specific project
    await create_user(
        developer_id=developer_id,
        data=CreateUserRequest(
            name="test user for project filter",
            about="test user about",
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]

    # Now fetch with project filter
    result = await list_users(
        developer_id=developer_id, project=project.canonical_name, connection_pool=pool
    )  # type: ignore[not-callable]

    assert isinstance(result, list)
    assert all(isinstance(user, User) for user in result)
    assert all(user.project == project.canonical_name for user in result)


@test("query: list users sql, invalid limit")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing users with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_users(
            developer_id=developer_id,
            limit=101,
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"

    with raises(HTTPException) as exc:
        await list_users(
            developer_id=developer_id,
            limit=0,
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"


@test("query: list users sql, invalid offset")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing users with an invalid offset raises an exception."""
    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_users(
            developer_id=developer_id,
            connection_pool=pool,
            offset=-1,
        )  # type: ignore[not-callable]

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Offset must be non-negative"


@test("query: list users sql, invalid sort by")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing users with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_users(
            developer_id=developer_id,
            connection_pool=pool,
            sort_by="invalid",
        )  # type: ignore[not-callable]

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort field"


@test("query: list users sql, invalid sort direction")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing users with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_users(
            developer_id=developer_id,
            connection_pool=pool,
            sort_by="created_at",
            direction="invalid",
        )  # type: ignore[not-callable]

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort direction"


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
    )  # type: ignore[not-callable]
    assert patch_result is not None
    assert isinstance(patch_result, User)
    assert patch_result.updated_at > user.created_at


@test("query: patch user with project sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, user=test_user, project=test_project):
    """Test that a user can be successfully patched with a project."""

    pool = await create_db_pool(dsn=dsn)
    patch_result = await patch_user(
        developer_id=developer_id,
        user_id=user.id,
        data=PatchUserRequest(
            name="patched user with project",
            about="patched user about",
            metadata={"test": "metadata"},
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    assert patch_result is not None
    assert isinstance(patch_result, User)
    assert patch_result.updated_at > user.created_at
    assert patch_result.project == project.canonical_name


@test("query: delete user sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, user=test_user):
    """Test that a user can be successfully deleted."""

    pool = await create_db_pool(dsn=dsn)
    delete_result = await delete_user(
        developer_id=developer_id,
        user_id=user.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert delete_result is not None
    assert isinstance(delete_result, ResourceDeletedResponse)

    # Verify the user no longer exists
    try:
        await get_user(
            developer_id=developer_id,
            user_id=user.id,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    except Exception:
        pass
    else:
        assert False, "Expected an exception to be raised when retrieving a deleted user."
