# Tests for user queries
from pycozo import Client
from uuid import uuid4
from ward import test

from .create_user import create_user_query
from .get_user import get_user_query
from .list_users import list_users_query
from .schema import init


def cozo_client():
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)

    return client


@test("create user")
def _():
    client = cozo_client()
    user_id = uuid4()

    query = create_user_query(
        user_id=user_id,
        name="test user",
        about="test user about",
    )

    result = client.run(query)


@test("get user not exists")
def _():
    client = cozo_client()
    user_id = uuid4()

    query = get_user_query(
        user_id=user_id,
    )

    result = client.run(query)

    assert len(result["user_id"]) == 0


@test("get user exists")
def _():
    client = cozo_client()
    user_id = uuid4()

    query = create_user_query(
        user_id=user_id,
        name="test user",
        about="test user about",
    )

    client.run(query)

    query = get_user_query(
        user_id=user_id,
    )

    result = client.run(query)

    assert len(result["user_id"]) == 1


@test("list users")
def _():
    client = cozo_client()
    user_id = uuid4()

    query = list_users_query()

    result = client.run(query)

    assert len(result["user_id"]) == 0
