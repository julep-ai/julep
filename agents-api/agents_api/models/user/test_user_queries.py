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
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("model: create user")
def _():
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
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    # Should fail because the user already exists.
    with raises(Exception):
        create_user_query(
            user_id=user_id,
            developer_id=developer_id,
            name="test user",
            about="test user about",
            client=client,
        )


@test("model: update non-existent user should fail")
def _():
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    # Should fail because the user doecn't exists.
    with raises(None):
        update_user_query(
            user_id=user_id,
            developer_id=developer_id,
            name="test user",
            about="test user about",
            client=client,
        )


@test("model: update user")
def _():
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
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    result = get_user_query(
        user_id=user_id,
        developer_id=developer_id,
        client=client,
    )

    assert len(result["id"]) == 0


@test("model: get user exists")
def _():
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
    client = cozo_client()
    developer_id = uuid4()

    result = list_users_query(
        developer_id=developer_id,
        client=client,
    )

    assert len(result["id"]) == 0
