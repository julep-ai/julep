"""Tests for entry queries."""

from agents_api.autogen.openapi_model import CreateEntryRequest, CreateSessionRequest
from agents_api.clients.pg import create_db_pool
from agents_api.queries.entries.count_entries import count_entries
from agents_api.queries.entries.create_entries import create_entries
from agents_api.queries.sessions.create_session import create_session
from ward import test

from tests.fixtures import pg_dsn, test_agent, test_developer_id


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
    assert count_result["count"] == 1
