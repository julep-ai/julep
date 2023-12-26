# Tests for entry queries
from pycozo import Client
from uuid import uuid4
from ward import test

from ...common.protocol.entries import Entry
from .add_entries import add_entries_query
from .get_entries import get_entries_query
from .naive_context_window import naive_context_window_query
from .schema import init


def cozo_client():
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)

    return client


@test("create entry without returning")
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
