# Tests for entry queries
from uuid import uuid4

from cozo_migrate.api import init, apply
from pycozo import Client
from ward import test

from ...common.protocol.entries import Entry
from .add_entries import add_entries_query
from .get_entries import get_entries_query
from .naive_context_window import naive_context_window_query


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("create entry")
def _():
    client = cozo_client()
    session_id = uuid4()

    test_entry = Entry(
        session_id=session_id,
        role="user",
        content="test entry content",
    )

    query = add_entries_query(
        entries=[test_entry],
    )

    client.run(query)


@test("get entries")
def _():
    client = cozo_client()
    session_id = uuid4()

    test_entry = Entry(
        session_id=session_id,
        role="user",
        content="test entry content",
    )

    internal_entry = Entry(
        session_id=session_id,
        role="user",
        content="test entry content",
        source="internal",
    )

    query = add_entries_query(
        entries=[test_entry, internal_entry],
    )

    client.run(query)

    query = get_entries_query(
        session_id=session_id,
    )

    result = client.run(query)

    assert len(result["entry_id"]) == 1


@test("naive context window")
def _():
    client = cozo_client()
    session_id = uuid4()

    test_entry = Entry(
        session_id=session_id,
        role="user",
        content="test entry content",
    )

    query = add_entries_query(
        entries=[test_entry],
    )

    client.run(query)

    query = naive_context_window_query(
        session_id=session_id,
    )

    result = client.run(query)

    assert len(result["created_at"]) == 1
