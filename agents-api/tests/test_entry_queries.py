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
import pytest

from tests.fixtures import pg_dsn, test_developer, test_developer_id, test_session

MODEL = "gpt-4o-mini"


@pytest.mark.asyncio
async def test_query_create_entry_no_session(dsn=pg_dsn, developer=test_developer):
    """query: create entry no session"""
    """Test the addition of a new entry to the database."""

    pool = await create_db_pool(dsn=dsn)
    test_entry = CreateEntryRequest.from_model_input(
        model=MODEL,
        role="user",
        source="internal",
        content="test entry content",
    )

    with pytest.pytest.raises(HTTPException) as exc_info:
        await create_entries(
            developer_id=developer.id,
            session_id=uuid7(),
            data=[test_entry],
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 404


@pytest.mark.asyncio
async def test_query_list_entries_sql_no_session(dsn=pg_dsn, developer=test_developer):
    """query: list entries sql - no session"""
    """Test the retrieval of entries from the database."""

    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer.id,
            session_id=uuid7(),
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 404


@pytest.mark.asyncio
async def test_query_list_entries_sql_invalid_limit(dsn=pg_dsn, developer_id=test_developer_id):
    """query: list entries sql, invalid limit"""
    """Test that listing entries with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer_id,
            session_id=uuid7(),
            limit=1001,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 400
    assert exc_info.raised.detail == "Limit must be between 1 and 1000"

    with pytest.pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer_id,
            session_id=uuid7(),
            limit=0,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 400
    assert exc_info.raised.detail == "Limit must be between 1 and 1000"


@pytest.mark.asyncio
async def test_query_list_entries_sql_invalid_offset(dsn=pg_dsn, developer_id=test_developer_id):
    """query: list entries sql, invalid offset"""
    """Test that listing entries with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer_id,
            session_id=uuid7(),
            offset=-1,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 400
    assert exc_info.raised.detail == "Offset must be >= 0"


@pytest.mark.asyncio
async def test_query_list_entries_sql_invalid_sort_by(dsn=pg_dsn, developer_id=test_developer_id):
    """query: list entries sql, invalid sort by"""
    """Test that listing entries with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer_id,
            session_id=uuid7(),
            sort_by="invalid",
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 400
    assert exc_info.raised.detail == "Invalid sort field"


@pytest.mark.asyncio
async def test_query_list_entries_sql_invalid_sort_direction(dsn=pg_dsn, developer_id=test_developer_id):
    """query: list entries sql, invalid sort direction"""
    """Test that listing entries with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer_id,
            session_id=uuid7(),
            direction="invalid",
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 400
    assert exc_info.raised.detail == "Invalid sort direction"


@pytest.mark.asyncio
async def test_query_list_entries_sql_session_exists(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """query: list entries sql - session exists"""
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


@pytest.mark.asyncio
async def test_query_get_history_sql_session_exists(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """query: get history sql - session exists"""
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


@pytest.mark.asyncio
async def test_query_delete_entries_sql_session_exists(dsn=pg_dsn, developer_id=test_developer_id, session=test_session):
    """query: delete entries sql - session exists"""
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
