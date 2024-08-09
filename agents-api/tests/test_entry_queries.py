"""
This module contains tests for entry queries against the CozoDB database.
It verifies the functionality of adding, retrieving, and processing entries as defined in the schema.
"""

# Tests for entry queries

from ward import test

from agents_api.autogen.openapi_model import CreateEntryRequest
from agents_api.models.entry.create_entries import create_entries
from agents_api.models.entry.list_entries import list_entries
from agents_api.models.entry.delete_entries import delete_entries
from tests.fixtures import cozo_client, test_developer_id, test_session

MODEL = "julep-ai/samantha-1-turbo"


@test("model: create entry")
def _(client=cozo_client, developer_id=test_developer_id, session=test_session):
    """
    Tests the addition of a new entry to the database.
    Verifies that the entry can be successfully added using the create_entries function.
    """

    test_entry = CreateEntryRequest(
        session_id=session.id,
        role="user",
        source="internal",
        content="test entry content",
    )

    create_entries(
        developer_id=developer_id,
        session_id=session.id,
        data=[test_entry],
        client=client,
    )


@test("model: get entries")
def _(client=cozo_client, developer_id=test_developer_id, session=test_session):
    """
    Tests the retrieval of entries from the database.
    Verifies that entries matching specific criteria can be successfully retrieved.
    """

    test_entry = CreateEntryRequest(
        session_id=session.id,
        role="user",
        source="api_request",
        content="test entry content",
    )

    internal_entry = CreateEntryRequest(
        session_id=session.id,
        role="user",
        content="test entry content",
        source="internal",
    )

    create_entries(
        developer_id=developer_id,
        session_id=session.id,
        data=[test_entry, internal_entry],
        client=client,
    )

    result = list_entries(
        developer_id=developer_id,
        session_id=session.id,
        client=client,
    )

    # Asserts that only one entry is retrieved, matching the session_id.
    assert len(result) == 1


@test("model: delete entries")
def _(client=cozo_client, developer_id=test_developer_id, session=test_session):
    """
    Tests the deletion of entries from the database.
    Verifies that entries can be successfully deleted using the delete_entries function.
    """

    test_entry = CreateEntryRequest(
        session_id=session.id,
        role="user",
        source="api_request",
        content="test entry content",
    )

    internal_entry = CreateEntryRequest(
        session_id=session.id,
        role="user",
        content="test entry content",
        source="internal",
    )

    created_entries = create_entries(
        developer_id=developer_id,
        session_id=session.id,
        data=[test_entry, internal_entry],
        client=client,
    )

    entry_ids = [entry.id for entry in created_entries]

    delete_entries(
        developer_id=developer_id,
        session_id=session.id,
        entry_ids=entry_ids,
        client=client,
    )

    result = list_entries(
        developer_id=developer_id,
        session_id=session.id,
        client=client,
    )

    # Asserts that no entries are retrieved after deletion.
    assert len(result) == 0
