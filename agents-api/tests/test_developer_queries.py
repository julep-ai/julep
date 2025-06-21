# Tests for developer queries

import pytest
from agents_api.clients.pg import create_db_pool
from agents_api.common.protocol.developers import Developer
from agents_api.queries.developers.create_developer import create_developer
from agents_api.queries.developers.get_developer import (
    get_developer,
)
from agents_api.queries.developers.patch_developer import patch_developer
from agents_api.queries.developers.update_developer import update_developer
from uuid_extensions import uuid7


async def test_query_get_developer_not_exists(pg_dsn):
    """Test that getting a non-existent developer raises an exception."""
    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(Exception):
        await get_developer(
            developer_id=uuid7(),
            connection_pool=pool,
        )


async def test_query_get_developer_exists(pg_dsn, test_new_developer):
    """Test that getting an existing developer returns the correct developer."""
    pool = await create_db_pool(dsn=pg_dsn)
    developer = await get_developer(
        developer_id=test_new_developer.id,
        connection_pool=pool,
    )

    assert type(developer) is Developer
    assert developer.id == test_new_developer.id
    assert developer.email == test_new_developer.email
    assert developer.active
    assert developer.tags == test_new_developer.tags
    assert developer.settings == test_new_developer.settings


async def test_query_create_developer(pg_dsn):
    """Test that a developer can be successfully created."""
    pool = await create_db_pool(dsn=pg_dsn)
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


async def test_query_update_developer(pg_dsn, test_new_developer, random_email):
    """Test that a developer can be successfully updated."""
    pool = await create_db_pool(dsn=pg_dsn)
    developer = await update_developer(
        email=random_email,
        tags=["tag2"],
        settings={"key2": "val2"},
        developer_id=test_new_developer.id,
        connection_pool=pool,
    )

    assert developer.id == test_new_developer.id


async def test_query_patch_developer(pg_dsn, test_new_developer, random_email):
    """Test that a developer can be successfully patched."""
    pool = await create_db_pool(dsn=pg_dsn)
    developer = await patch_developer(
        email=random_email,
        active=True,
        tags=["tag2"],
        settings={"key2": "val2"},
        developer_id=test_new_developer.id,
        connection_pool=pool,
    )

    assert developer.id == test_new_developer.id
    assert developer.email == random_email
    assert developer.active
    assert developer.tags == [*test_new_developer.tags, "tag2"]
    assert developer.settings == {**test_new_developer.settings, "key2": "val2"}