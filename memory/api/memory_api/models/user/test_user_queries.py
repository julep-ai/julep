# Tests for user queries
from uuid import uuid4

from cozo_migrate.api import init, apply
from pycozo import Client
from ward import raises, test, skip

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


@test("create user")
def _():
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    query = create_user_query(
        user_id=user_id,
        developer_id=developer_id,
        name="test user",
        about="test user about",
    )

    client.run(query)


@test("create user twice should fail")
def _():
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    query = create_user_query(
        user_id=user_id,
        developer_id=developer_id,
        name="test user",
        about="test user about",
    )

    client.run(query)

    # Should fail because the user already exists.
    with raises(Exception):
        client.run(query)


@test("update non-existent user should fail")
def _():
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    query = update_user_query(
        user_id=user_id,
        developer_id=developer_id,
        name="test user",
        about="test user about",
    )

    # Should fail because the user doecn't exists.
    with raises(Exception):
        client.run(query)


@test("update user")
def _():
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    create_query = create_user_query(
        user_id=user_id,
        developer_id=developer_id,
        name="test user",
        about="test user about",
    )

    client.run(create_query)

    update_query = update_user_query(
        user_id=user_id,
        developer_id=developer_id,
        name="updated user",
        about="updated user about",
    )

    result = client.run(update_query)
    data = result.iloc[0].to_dict()

    assert data["updated_at"] > data["created_at"]


@test("get user not exists")
def _():
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    query = get_user_query(
        user_id=user_id,
        developer_id=developer_id,
    )

    result = client.run(query)

    assert len(result["id"]) == 0


@test("get user exists")
def _():
    client = cozo_client()
    user_id = uuid4()
    developer_id = uuid4()

    query = create_user_query(
        user_id=user_id,
        developer_id=developer_id,
        name="test user",
        about="test user about",
    )

    client.run(query)

    query = get_user_query(
        user_id=user_id,
        developer_id=developer_id,
    )

    result = client.run(query)

    assert len(result["id"]) == 1


@test("list users")
def _():
    client = cozo_client()
    developer_id = uuid4()

    query = list_users_query(
        developer_id=developer_id,
    )

    result = client.run(query)

    assert len(result["id"]) == 0
