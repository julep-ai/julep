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


MODEL = "gpt-4o-mini"


async def test_query_create_entry_no_session(pg_dsn, test_developer):
    """Test the addition of a new entry to the database."""

    pool = await create_db_pool(dsn=pg_dsn)
    test_entry = CreateEntryRequest.from_model_input(
        model=MODEL,
        role="user",
        source="internal",
        content="test entry content",
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_entries(
            developer_id=test_developer.id,
            session_id=uuid7(),
            data=[test_entry],
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.value.status_code == 404


async def test_query_list_entries_sql_no_session(pg_dsn, test_developer):
    """Test the retrieval of entries from the database."""

    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=test_developer.id,
            session_id=uuid7(),
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.value.status_code == 404


async def test_query_list_entries_sql_invalid_limit(pg_dsn, test_developer_id):
    """Test that listing entries with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=test_developer_id,
            session_id=uuid7(),
            limit=1001,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Limit must be between 1 and 1000"

    with pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=test_developer_id,
            session_id=uuid7(),
            limit=0,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Limit must be between 1 and 1000"


async def test_query_list_entries_sql_invalid_offset(pg_dsn, test_developer_id):
    """Test that listing entries with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=test_developer_id,
            session_id=uuid7(),
            offset=-1,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Offset must be >= 0"


async def test_query_list_entries_sql_invalid_sort_by(pg_dsn, test_developer_id):
    """Test that listing entries with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=test_developer_id,
            session_id=uuid7(),
            sort_by="invalid",
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid sort field"


async def test_query_list_entries_sql_invalid_sort_direction(pg_dsn, test_developer_id):
    """Test that listing entries with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=test_developer_id,
            session_id=uuid7(),
            direction="invalid",
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid sort direction"


async def test_query_list_entries_sql_session_exists(pg_dsn, test_developer_id, test_session):
    """Test the retrieval of entries from the database."""

    pool = await create_db_pool(dsn=pg_dsn)
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
        developer_id=test_developer_id,
        session_id=test_session.id,
        data=[test_entry, internal_entry],
        connection_pool=pool,
    )  # type: ignore[not-callable]

    result = await list_entries(
        developer_id=test_developer_id,
        session_id=test_session.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    # Assert that only one entry is retrieved, matching the session_id.
    assert len(result) == 1
    assert isinstance(result[0], Entry)
    assert result is not None


async def test_query_get_history_sql_session_exists(pg_dsn, test_developer_id, test_session):
    """Test the retrieval of entry history from the database."""

    pool = await create_db_pool(dsn=pg_dsn)
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
        developer_id=test_developer_id,
        session_id=test_session.id,
        data=[test_entry, internal_entry],
        connection_pool=pool,
    )  # type: ignore[not-callable]

    result = await get_history(
        developer_id=test_developer_id,
        session_id=test_session.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    # Assert that entries are retrieved and have valid IDs.
    assert result is not None
    assert isinstance(result, History)
    assert len(result.entries) > 0
    assert result.entries[0].id


async def test_query_delete_entries_sql_session_exists(pg_dsn, test_developer_id, test_session):
    """Test the deletion of entries from the database."""

    pool = await create_db_pool(dsn=pg_dsn)
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
        developer_id=test_developer_id,
        session_id=test_session.id,
        data=[test_entry, internal_entry],
        connection_pool=pool,
    )  # type: ignore[not-callable]

    entry_ids = [entry.id for entry in created_entries]

    await delete_entries(
        developer_id=test_developer_id,
        session_id=test_session.id,
        entry_ids=entry_ids,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    result = await list_entries(
        developer_id=test_developer_id,
        session_id=test_session.id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    # Assert that no entries are retrieved after deletion.
    assert all(id not in [entry.id for entry in result] for id in entry_ids)
    assert len(result) == 0
    assert result is not None
