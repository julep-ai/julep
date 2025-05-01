"""
This module contains tests for entry queries against the CozoDB database.
It verifies the functionality of adding, retrieving, and processing entries as defined in the schema.
"""

from unittest.mock import MagicMock, patch

from agents_api.app import app
from agents_api.autogen.openapi_model import (
    CreateEntryRequest,
    CreateSessionRequest,
    Entry,
    History,
)
from agents_api.clients.pg import create_db_pool
from agents_api.env import max_free_entries
from agents_api.queries.entries import (
    create_entries,
    delete_entries,
    get_history,
    list_entries,
)
from agents_api.queries.entries.count_entries import count_entries
from agents_api.queries.sessions.create_session import create_session
from agents_api.routers.sessions.render import render_chat_input
from fastapi import HTTPException
from uuid_extensions import uuid7
from ward import raises, test

from tests.fixtures import pg_dsn, test_agent, test_developer, test_developer_id, test_session

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


@test("query: list entries sql, invalid limit")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing entries with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer_id,
            session_id=uuid7(),
            limit=1001,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 400
    assert exc_info.raised.detail == "Limit must be between 1 and 1000"

    with raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer_id,
            session_id=uuid7(),
            limit=0,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 400
    assert exc_info.raised.detail == "Limit must be between 1 and 1000"


@test("query: list entries sql, invalid offset")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing entries with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer_id,
            session_id=uuid7(),
            offset=-1,
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 400
    assert exc_info.raised.detail == "Offset must be >= 0"


@test("query: list entries sql, invalid sort by")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing entries with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer_id,
            session_id=uuid7(),
            sort_by="invalid",
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 400
    assert exc_info.raised.detail == "Invalid sort field"


@test("query: list entries sql, invalid sort direction")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing entries with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with raises(HTTPException) as exc_info:
        await list_entries(
            developer_id=developer_id,
            session_id=uuid7(),
            direction="invalid",
            connection_pool=pool,
        )  # type: ignore[not-callable]
    assert exc_info.raised.status_code == 400
    assert exc_info.raised.detail == "Invalid sort direction"


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


@test("render: free tier entry limit exceeded")
async def _(session=test_session, dsn=pg_dsn):
    """Test that a free tier user cannot exceed the maximum number of entries."""

    pool = await create_db_pool(dsn=dsn)
    app.state.postgres_pool = pool

    # Create a mock developer without the "paid" tag
    mock_developer = MagicMock()
    mock_developer.id = uuid7()
    mock_developer.tags = []

    # Create a mock chat input
    mock_chat_input = MagicMock()

    # Mock the count_entries function to return a count exceeding the free tier limit
    with (
        patch("agents_api.routers.sessions.render.count_entries") as mock_count_entries,
        patch("agents_api.routers.sessions.render.count_sessions_query") as mock_count_sessions,
    ):
        # Set up mock return values
        mock_count_sessions.return_value = {"count": 10}  # Below the session limit
        mock_count_entries.return_value = {
            "count": max_free_entries + 1
        }  # Exceed the entry limit

        # Attempt to render chat input which should trigger the free tier limit check
        with raises(HTTPException) as exc_info:
            await render_chat_input(
                developer=mock_developer,
                session_id=session.id,
                chat_input=mock_chat_input,
            )

        # Verify the correct exception is raised
        assert exc_info.raised.status_code == 403
        assert exc_info.raised.detail == "Entry count exceeded the free tier limit"

        # Verify our mocks were called with the correct parameters
        mock_count_entries.assert_called_once_with(developer_id=mock_developer.id)


@test("query: count entries by developer")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)
    # Create a test session first
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            name="Test Session",
            description="Test session for counting entries",
            metadata={"test": True},
            agent=agent.id,
        ),
        connection_pool=pool,
    )

    # Create a test entry in the session
    await create_entries(
        developer_id=developer_id,
        session_id=session.id,
        data=[
            CreateEntryRequest(
                content="Test entry content",
                role="user",
                metadata={"test": True},
                source="api_request",
                tokenizer="gpt-4o-mini",
                token_count=10,
            )
        ],
        connection_pool=pool,
    )
    count_result = await count_entries(
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert count_result is not None
    assert isinstance(count_result, dict)
    assert "count" in count_result
    assert isinstance(count_result["count"], int)
    assert count_result["count"] > 1
