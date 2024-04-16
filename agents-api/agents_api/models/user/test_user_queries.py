"""This module contains tests for user-related queries against the 'cozodb' database. It includes tests for creating, updating, and retrieving user information."""

# Tests for user queries
from uuid import uuid4

from cozo_migrate.api import init, apply
from pycozo import Client
from ward import raises, test

from .create_user import create_user_query
from .get_user import get_user_query
from .list_users import list_users_query
from .update_user import update_user_query


def cozo_client(migrations_dir: str = "./migrations"):
    """Initializes a new Cozo client for testing, applying all migrations to ensure the database schema is up to date."""
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("model: create user")
def _():
    """Test that a user can be successfully created."""
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    create_user_query(
        user_id=user_id,
        developer_id=developer_id,
        name="test user",
        about="test user about",
        client=client,
    )


@test("model: create user twice should fail")
def _():
    """Test that attempting to create the same user twice results in a failure."""
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    # Expect an exception to be raised as creating the same user twice should not be allowed.
    # Should fail because the user already exists.
    with raises(Exception):
        create_user_query(
            user_id=user_id,
            developer_id=developer_id,
            name="test user",
            about="test user about",
            client=client,
        )

        create_user_query(
            user_id=user_id,
            developer_id=developer_id,
            name="test user",
            about="test user about",
            client=client,
        )


@test("model: update non-existent user should fail")
def _():
    """Test that attempting to update a non-existent user results in a failure."""
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    # Should fail because the user doecn't exists.
    with raises(Exception):
        update_user_query(
            user_id=user_id,
            developer_id=developer_id,
            name="test user",
            about="test user about",
            client=client,
        )


@test("model: update user")
def _():
    """Test that an existing user's information can be successfully updated."""
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    create_user_query(
        user_id=user_id,
        developer_id=developer_id,
        name="test user",
        about="test user about",
        client=client,
    )

    # Verify that the 'updated_at' timestamp is greater than the 'created_at' timestamp, indicating a successful update.
    update_result = update_user_query(
        user_id=user_id,
        developer_id=developer_id,
        name="updated user",
        about="updated user about",
        client=client,
    )

    data = update_result.iloc[0].to_dict()

    assert data["updated_at"] > data["created_at"]


@test("model: get user not exists")
def _():
    """Test that retrieving a non-existent user returns an empty result."""
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    # Ensure that the query for an existing user returns exactly one result.
    result = get_user_query(
        user_id=user_id,
        developer_id=developer_id,
        client=client,
    )

    assert len(result["id"]) == 0


@test("model: get user exists")
def _():
    """Test that retrieving an existing user returns the correct user information."""
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    result = create_user_query(
        user_id=user_id,
        developer_id=developer_id,
        name="test user",
        about="test user about",
        client=client,
    )

    result = get_user_query(
        user_id=user_id,
        developer_id=developer_id,
        client=client,
    )

    assert len(result["id"]) == 1


@test("model: list users")
def _():
    """Test that listing users returns a collection of user information."""
    client = cozo_client()
    developer_id = uuid4()

    result = list_users_query(
        developer_id=developer_id,
        client=client,
    )

    assert len(result["id"]) == 0
