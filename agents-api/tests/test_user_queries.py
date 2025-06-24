"""
This module contains tests for SQL query generation functions in the users module.
Tests verify the SQL queries without actually executing them against a database.
"""

from uuid import UUID

import pytest
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

# Test UUIDs for consistent testing
TEST_DEVELOPER_ID = UUID("123e4567-e89b-12d3-a456-426614174000")
TEST_USER_ID = UUID("987e6543-e21b-12d3-a456-426614174000")


async def test_query_create_user_sql(pg_dsn, test_developer_id):
    """Test that a user can be successfully created."""

    pool = await create_db_pool(dsn=pg_dsn)
    user = await create_user(
        developer_id=test_developer_id,
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


async def test_query_create_user_with_project_sql(pg_dsn, test_developer_id, test_project):
    """Test that a user can be successfully created with a project."""

    pool = await create_db_pool(dsn=pg_dsn)
    user = await create_user(
        developer_id=test_developer_id,
        data=CreateUserRequest(
            name="test user with project",
            about="test user about",
            project=test_project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    assert isinstance(user, User)
    assert user.id is not None
    assert user.project == test_project.canonical_name


async def test_query_create_user_with_invalid_project_sql(pg_dsn, test_developer_id):
    """Test that creating a user with an invalid project raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc:
        await create_user(
            developer_id=test_developer_id,
            data=CreateUserRequest(
                name="test user with invalid project",
                about="test user about",
                project="invalid_project",
            ),
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.value.status_code == 404
    assert "Project 'invalid_project' not found" in exc.value.detail


async def test_query_create_or_update_user_sql(pg_dsn, test_developer_id):
    """Test that a user can be successfully created or updated."""

    pool = await create_db_pool(dsn=pg_dsn)
    user = await create_or_update_user(
        developer_id=test_developer_id,
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


async def test_query_create_or_update_user_with_project_sql(
    pg_dsn, test_developer_id, test_project
):
    """Test that a user can be successfully created or updated with a project."""

    pool = await create_db_pool(dsn=pg_dsn)
    user = await create_or_update_user(
        developer_id=test_developer_id,
        user_id=uuid7(),
        data=CreateOrUpdateUserRequest(
            name="test user with project",
            about="test user about",
            project=test_project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    assert isinstance(user, User)
    assert user.id is not None
    assert user.project == test_project.canonical_name


async def test_query_update_user_sql(pg_dsn, test_developer_id, test_user):
    """Test that an existing user's information can be successfully updated."""

    pool = await create_db_pool(dsn=pg_dsn)
    update_result = await update_user(
        user_id=test_user.id,
        developer_id=test_developer_id,
        data=UpdateUserRequest(
            name="updated user",
            about="updated user about",
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert update_result is not None
    assert isinstance(update_result, User)
    assert update_result.updated_at > test_user.created_at


async def test_query_update_user_with_project_sql(
    pg_dsn, test_developer_id, test_user, test_project
):
    """Test that an existing user's information can be successfully updated with a project."""

    pool = await create_db_pool(dsn=pg_dsn)
    update_result = await update_user(
        user_id=test_user.id,
        developer_id=test_developer_id,
        data=UpdateUserRequest(
            name="updated user with project",
            about="updated user about",
            project=test_project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    # Verify the user was updated by listing all users
    users = await list_users(
        developer_id=test_developer_id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert users is not None
    assert isinstance(users, list)
    assert len(users) > 0

    # Find the updated user in the list
    updated_user = next((u for u in users if u.id == test_user.id), None)
    assert updated_user is not None
    assert updated_user.name == "updated user with project"
    assert updated_user.project == test_project.canonical_name

    assert update_result is not None
    assert isinstance(update_result, User)
    assert update_result.updated_at > test_user.created_at
    assert update_result.project == test_project.canonical_name


async def test_query_update_user_project_does_not_exist(pg_dsn, test_developer_id, test_user):
    """Test that an existing user's information can be successfully updated with a project that does not exist."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await update_user(
            user_id=test_user.id,
            developer_id=test_developer_id,
            data=UpdateUserRequest(
                name="updated user with project",
                about="updated user about",
                project="invalid_project",
            ),
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.value.status_code == 404
    assert "Project 'invalid_project' not found" in exc.value.detail


async def test_query_get_user_not_exists_sql(pg_dsn, test_developer_id):
    """Test that retrieving a non-existent user returns an empty result."""

    user_id = uuid7()

    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(Exception):
        await get_user(
            user_id=user_id,
            developer_id=test_developer_id,
            connection_pool=pool,
        )  # type: ignore[not-callable]


async def test_query_get_user_exists_sql(pg_dsn, test_developer_id, test_user):
    """Test that retrieving an existing user returns the correct user information."""

    pool = await create_db_pool(dsn=pg_dsn)
    result = await get_user(
        user_id=test_user.id,
        developer_id=test_developer_id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, User)


async def test_query_list_users_sql(pg_dsn, test_developer_id, test_user):
    """Test that listing users returns a collection of user information."""

    pool = await create_db_pool(dsn=pg_dsn)
    result = await list_users(
        developer_id=test_developer_id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(isinstance(user, User) for user in result)


async def test_query_list_users_with_project_filter_sql(
    pg_dsn, test_developer_id, test_project
):
    """Test that listing users with a project filter returns the correct users."""

    pool = await create_db_pool(dsn=pg_dsn)

    # First create a user with the specific project
    await create_user(
        developer_id=test_developer_id,
        data=CreateUserRequest(
            name="test user for project filter",
            about="test user about",
            project=test_project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]

    # Now fetch with project filter
    result = await list_users(
        developer_id=test_developer_id,
        project=test_project.canonical_name,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert isinstance(result, list)
    assert all(isinstance(user, User) for user in result)
    assert all(user.project == test_project.canonical_name for user in result)


async def test_query_list_users_sql_invalid_limit(pg_dsn, test_developer_id):
    """Test that listing users with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_users(
            developer_id=test_developer_id,
            limit=101,
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.value.status_code == 400
    assert exc.value.detail == "Limit must be between 1 and 100"

    with pytest.raises(HTTPException) as exc:
        await list_users(
            developer_id=test_developer_id,
            limit=0,
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.value.status_code == 400
    assert exc.value.detail == "Limit must be between 1 and 100"


async def test_query_list_users_sql_invalid_offset(pg_dsn, test_developer_id):
    """Test that listing users with an invalid offset raises an exception."""
    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_users(
            developer_id=test_developer_id,
            connection_pool=pool,
            offset=-1,
        )  # type: ignore[not-callable]

    assert exc.value.status_code == 400
    assert exc.value.detail == "Offset must be non-negative"


async def test_query_list_users_sql_invalid_sort_by(pg_dsn, test_developer_id):
    """Test that listing users with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_users(
            developer_id=test_developer_id,
            connection_pool=pool,
            sort_by="invalid",
        )  # type: ignore[not-callable]

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort field"


async def test_query_list_users_sql_invalid_sort_direction(pg_dsn, test_developer_id):
    """Test that listing users with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_users(
            developer_id=test_developer_id,
            connection_pool=pool,
            sort_by="created_at",
            direction="invalid",
        )  # type: ignore[not-callable]

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort direction"


async def test_query_patch_user_sql(pg_dsn, test_developer_id, test_user):
    """Test that a user can be successfully patched."""

    pool = await create_db_pool(dsn=pg_dsn)
    patch_result = await patch_user(
        developer_id=test_developer_id,
        user_id=test_user.id,
        data=PatchUserRequest(
            name="patched user",
            about="patched user about",
            metadata={"test": "metadata"},
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    assert patch_result is not None
    assert isinstance(patch_result, User)
    assert patch_result.updated_at > test_user.created_at


async def test_query_patch_user_with_project_sql(
    pg_dsn, test_developer_id, test_user, test_project
):
    """Test that a user can be successfully patched with a project."""

    pool = await create_db_pool(dsn=pg_dsn)
    patch_result = await patch_user(
        developer_id=test_developer_id,
        user_id=test_user.id,
        data=PatchUserRequest(
            name="patched user with project",
            about="patched user about",
            metadata={"test": "metadata"},
            project=test_project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    # Verify the user was updated by listing all users
    users = await list_users(
        developer_id=test_developer_id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert users is not None
    assert isinstance(users, list)
    assert len(users) > 0

    # Find the updated user in the list
    updated_user = next((u for u in users if u.id == test_user.id), None)
    assert updated_user is not None
    assert updated_user.name == "patched user with project"
    assert updated_user.project == test_project.canonical_name

    assert patch_result is not None
    assert isinstance(patch_result, User)
    assert patch_result.updated_at > test_user.created_at
    assert patch_result.project == test_project.canonical_name


async def test_query_patch_user_project_does_not_exist(pg_dsn, test_developer_id, test_user):
    """Test that a user can be successfully patched with a project that does not exist."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await patch_user(
            developer_id=test_developer_id,
            user_id=test_user.id,
            data=PatchUserRequest(
                name="patched user with project",
                about="patched user about",
                metadata={"test": "metadata"},
                project="invalid_project",
            ),
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.value.status_code == 404
    assert "Project 'invalid_project' not found" in exc.value.detail


async def test_query_delete_user_sql(pg_dsn, test_developer_id, test_user):
    """Test that a user can be successfully deleted."""

    pool = await create_db_pool(dsn=pg_dsn)
    delete_result = await delete_user(
        developer_id=test_developer_id,
        user_id=test_user.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert delete_result is not None
    assert isinstance(delete_result, ResourceDeletedResponse)

    # Verify the user no longer exists
    try:
        await get_user(
            developer_id=test_developer_id,
            user_id=test_user.id,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    except Exception:
        pass
    else:
        assert False, "Expected an exception to be raised when retrieving a deleted user."
