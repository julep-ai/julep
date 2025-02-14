"""
This module contains tests for entry queries against the CozoDB database.
It verifies the functionality of adding, retrieving, and processing entries as defined in the schema.
"""

from agents_api.autogen.openapi_model import (
    CreateEntryRequest,
    Entry,
    History,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.entries import (
    create_entries,
    delete_entries,
    get_history,
    list_entries,
)
from fastapi import HTTPException
from uuid_extensions import uuid7
from ward import raises, test

from tests.fixtures import pg_dsn, test_developer, test_developer_id, test_session

MODEL = "gpt-4o-mini"


@test("query: create entry no session")
async def _(dsn=pg_dsn, developer=test_developer):
    """Test the addition of a new entry to the database."""

    pool = await create_db_pool(dsn=dsn)
    test_entry = CreateEntryRequest.from_model_input(
        model=MODEL,
        role="user",
        source="internal",
        content="test entry content",
    )

    with raises(HTTPException) as exc_info:
        await create_entries(
            developer_id=developer.id,
            session_id=uuid7(),
            data=[test_entry],
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 404


@test("query: list entries sql - no session")
async def _(dsn=pg_dsn, developer=test_developer):
    """Test the retrieval of entries from the database."""

    pool = await create_db_pool(dsn=dsn)

    with raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer.id,
            session_id=uuid7(),
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 404


@test("query: list entries sql - session exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """Test the retrieval of entries from the database."""

    pool = await create_db_pool(dsn=dsn)
    test_entry = CreateEntryRequest.from_model_input(
        model=MODEL,
        role="user",
        source="api_request",
        content="test entry content",
    )

    internal_entry = CreateEntryRequest.from_model_input(
        model=MODEL,
        role="user",
        content="test entry content",
        source="internal",
    )

    await create_entries(
        developer_id=developer_id,
        session_id=session.id,
        data=[test_entry, internal_entry],
        connection_pool=pool,
    )  # type: ignore[not-callable]

    result = await list_entries(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    # Assert that only one entry is retrieved, matching the session_id.
    assert len(result) == 1
    assert isinstance(result[0], Entry)
    assert result is not None


@test("query: get history sql - session exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """Test the retrieval of entry history from the database."""

    pool = await create_db_pool(dsn=dsn)
    test_entry = CreateEntryRequest.from_model_input(
        model=MODEL,
        role="user",
        source="api_request",
        content="test entry content",
    )

    internal_entry = CreateEntryRequest.from_model_input(
        model=MODEL,
        role="user",
        content="test entry content",
        source="internal",
    )

    await create_entries(
        developer_id=developer_id,
        session_id=session.id,
        data=[test_entry, internal_entry],
        connection_pool=pool,
    )  # type: ignore[not-callable]

    result = await get_history(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    # Assert that entries are retrieved and have valid IDs.
    assert result is not None
    assert isinstance(result, History)
    assert len(result.entries) > 0
    assert result.entries[0].id


@test("query: delete entries sql - session exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """Test the deletion of entries from the database."""

    pool = await create_db_pool(dsn=dsn)
    test_entry = CreateEntryRequest.from_model_input(
        model=MODEL,
        role="user",
        source="api_request",
        content="test entry content",
    )

    internal_entry = CreateEntryRequest.from_model_input(
        model=MODEL,
        role="user",
        content="internal entry content",
        source="internal",
    )

    created_entries = await create_entries(
        developer_id=developer_id,
        session_id=session.id,
        data=[test_entry, internal_entry],
        connection_pool=pool,
    )  # type: ignore[not-callable]

    entry_ids = [entry.id for entry in created_entries]

    await delete_entries(
        developer_id=developer_id,
        session_id=session.id,
        entry_ids=entry_ids,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    result = await list_entries(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    # Assert that no entries are retrieved after deletion.
    assert all(id not in [entry.id for entry in result] for id in entry_ids)
    assert len(result) == 0
    assert result is not None
