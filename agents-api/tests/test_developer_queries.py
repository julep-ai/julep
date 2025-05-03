# Tests for agent queries

from unittest.mock import patch
from uuid import uuid4

from agents_api.app import app
from agents_api.clients.pg import create_db_pool
from agents_api.common.protocol.developers import Developer
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.queries.developers.create_developer import create_developer
from agents_api.queries.developers.get_developer import (
    get_developer,
)
from agents_api.queries.developers.patch_developer import patch_developer
from agents_api.queries.developers.update_developer import update_developer
from fastapi import Depends
from fastapi.testclient import TestClient
from uuid_extensions import uuid7
from ward import raises, test

from .fixtures import pg_dsn, random_email, test_new_developer


@test("query: get developer not exists")
async def _(dsn=pg_dsn):
    pool = await create_db_pool(dsn=dsn)
    with raises(Exception):
        await get_developer(
            developer_id=uuid7(),
            connection_pool=pool,
        )


@test("query: get developer exists")
async def _(dsn=pg_dsn, dev=test_new_developer):
    pool = await create_db_pool(dsn=dsn)
    developer = await get_developer(
        developer_id=dev.id,
        connection_pool=pool,
    )

    assert type(developer) is Developer
    assert developer.id == dev.id
    assert developer.email == dev.email
    assert developer.active
    assert developer.tags == dev.tags
    assert developer.settings == dev.settings


@test("query: create developer")
async def _(dsn=pg_dsn):
    pool = await create_db_pool(dsn=dsn)
    dev_id = uuid7()
    developer = await create_developer(
        email="m@mail.com",
        active=True,
        tags=["tag1"],
        settings={"key1": "val1"},
        developer_id=dev_id,
        connection_pool=pool,
    )

    assert type(developer) is Developer
    assert developer.id == dev_id
    assert developer.created_at is not None


@test("query: update developer")
async def _(dsn=pg_dsn, dev=test_new_developer, email=random_email):
    pool = await create_db_pool(dsn=dsn)
    developer = await update_developer(
        email=email,
        tags=["tag2"],
        settings={"key2": "val2"},
        developer_id=dev.id,
        connection_pool=pool,
    )

    assert developer.id == dev.id


@test("query: patch developer")
async def _(dsn=pg_dsn, dev=test_new_developer, email=random_email):
    pool = await create_db_pool(dsn=dsn)
    developer = await patch_developer(
        email=email,
        active=True,
        tags=["tag2"],
        settings={"key2": "val2"},
        developer_id=dev.id,
        connection_pool=pool,
    )

    assert developer.id == dev.id
    assert developer.email == email
    assert developer.active
    assert developer.tags == [*dev.tags, "tag2"]
    assert developer.settings == {**dev.settings, "key2": "val2"}


@test("dependency: access denied for inactive developer")
async def _(dsn=pg_dsn):
    with patch("agents_api.dependencies.developer_id.multi_tenant_mode", True):
        developer_id = uuid4()
        # Add a test endpoint that requires authentication

        @app.get("/test")
        async def test_endpoint(x_developer_id=Depends(get_developer_id)):
            return {"message": "success"}

        # Create a test client
        client = TestClient(app)

        # Create an inactive developer
        pool = await create_db_pool(dsn=dsn)
        await create_developer(
            email="inactive@test.com",
            active=False,
            developer_id=developer_id,
            connection_pool=pool,
        )

        # Make a request with the inactive developer's ID
        response = client.get(
            "/test",
            headers={"X-Developer-Id": str(developer_id)},
        )

        # Verify we get a 403 response
        assert response.status_code == 403
        assert response.json()["error"]["message"] == "Invalid developer account"
