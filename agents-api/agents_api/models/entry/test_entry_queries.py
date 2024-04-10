# Tests for entry queries
from uuid import uuid4

from cozo_migrate.api import init, apply
from pycozo import Client
from ward import test

from ...autogen.openapi_model import FunctionDef
from ...common.protocol.entries import Entry
from ..docs.create_docs import create_docs_query
from ..docs.embed_docs import embed_docs_snippets_query
from ..agent.create_agent import create_agent_query
from ..session.create_session import create_session_query
from ..tools.create_tools import create_function_query
from ..tools.embed_tools import embed_functions_query
from ..user.create_user import create_user_query
from .add_entries import add_entries_query
from .get_entries import get_entries_query
from .naive_context_window import naive_context_window_query
from .proc_mem_context import proc_mem_context_query


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


@test("procedural memory context")
def _():
    client = cozo_client()
    developer_id = uuid4()
    user_id = uuid4()
    agent_id = uuid4()
    session_id = uuid4()
    tool_id = uuid4()
    user_doc_id = uuid4()
    agent_doc_id = uuid4()

    # Create stuff
    test_entry = Entry(
        session_id=session_id,
        role="user",
        content="test entry content",
        source="api_request",
    )

    test_instruction1 = "test instruction"
    test_instruction2 = "test instruction"
    test_function = FunctionDef(
        name="test function",
        description="test function description",
        parameters={"type": "object", "properties": {}},
    )

    test_user_doc = "test user doc"
    test_agent_doc = "test agent doc"

    queries = [
        add_entries_query(entries=[test_entry]),
        create_user_query(
            user_id=user_id,
            developer_id=developer_id,
            name="test user",
            about="test user about",
        ),
        create_agent_query(
            agent_id=agent_id,
            developer_id=developer_id,
            name="test agent",
            about="test agent about",
            instructions=[test_instruction1, test_instruction2],
        ),
        create_session_query(
            developer_id=developer_id,
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            situation="test situation",
        ),
        create_function_query(
            agent_id=agent_id,
            id=tool_id,
            function=test_function,
        ),
        create_docs_query(
            owner_type="agent",
            owner_id=agent_id,
            id=agent_doc_id,
            title=test_agent_doc,
            content=test_agent_doc,
        ),
        create_docs_query(
            owner_type="user",
            owner_id=user_id,
            id=user_doc_id,
            title=test_user_doc,
            content=test_user_doc,
        ),
        embed_functions_query(
            agent_id=agent_id,
            tool_ids=[tool_id],
            embeddings=[[1.0] * 768],
        ),
        embed_docs_snippets_query(
            agent_doc_id,
            snippet_indices=[0],
            embeddings=[[1.0] * 768],
        ),
        embed_docs_snippets_query(
            user_doc_id,
            snippet_indices=[0],
            embeddings=[[1.0] * 768],
        ),
    ]

    client.run("\n".join(queries))

    # Run the query
    query = proc_mem_context_query(
        session_id=session_id,
        tool_query_embedding=[0.9] * 768,
        doc_query_embedding=[0.9] * 768,
    )

    result = client.run(query)

    assert len(result) == 9
