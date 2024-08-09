# This module contains tests for user-related queries against the 'cozodb' database. It includes tests for creating, updating, and retrieving user information.

# Tests for user queries
from uuid import uuid4

from ward import test

from agents_api.autogen.openapi_model import (
    CreateUserRequest,
    ResourceUpdatedResponse,
    UpdateUserRequest,
    User,
)
from agents_api.models.user.create_user import create_user
from agents_api.models.user.get_user import get_user
from agents_api.models.user.list_users import list_users
from agents_api.models.user.update_user import update_user
from tests.fixtures import cozo_client, test_developer_id, test_user


@test("model: create user")
def _(client=cozo_client, developer_id=test_developer_id):
    """Test that a user can be successfully created."""

    create_user(
        developer_id=developer_id,
        data=CreateUserRequest(
            name="test user",
            about="test user about",
        ),
        client=client,
    )


@test("model: update user")
def _(client=cozo_client, developer_id=test_developer_id, user=test_user):
    """Test that an existing user's information can be successfully updated."""

    # Verify that the 'updated_at' timestamp is greater than the 'created_at' timestamp, indicating a successful update.
    update_result = update_user(
        user_id=user.id,
        developer_id=developer_id,
        data=UpdateUserRequest(
            name="updated user",
            about="updated user about",
        ),
        client=client,
    )

    assert update_result is not None
    assert isinstance(update_result, ResourceUpdatedResponse)
    assert update_result.updated_at > user.created_at


@test("model: get user not exists")
def _(client=cozo_client, developer_id=test_developer_id):
    """Test that retrieving a non-existent user returns an empty result."""

    user_id = uuid4()

    # Ensure that the query for an existing user returns exactly one result.
    try:
        get_user(
            user_id=user_id,
            developer_id=developer_id,
            client=client,
        )
    except Exception:
        pass
    else:
        assert (
            False
        ), "Expected an exception to be raised when retrieving a non-existent user."


@test("model: get user exists")
def _(client=cozo_client, developer_id=test_developer_id, user=test_user):
    """Test that retrieving an existing user returns the correct user information."""

    result = get_user(
        user_id=user.id,
        developer_id=developer_id,
        client=client,
    )

    assert result is not None
    assert isinstance(result, User)


@test("model: list users")
def _(client=cozo_client, developer_id=test_developer_id, user=test_user):
    """Test that listing users returns a collection of user information."""

    result = list_users(
        developer_id=developer_id,
        client=client,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(isinstance(user, User) for user in result)
