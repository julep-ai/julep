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

MODEL = "julep-ai/samantha-1-turbo"

def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("model: create entry")
def _():
    client = cozo_client()
    session_id = uuid4()

    test_entry = Entry(
        session_id=session_id,
        role="user",
        content="test entry content",
    )

    add_entries_query(entries=[test_entry], client=client)


@test("model: get entries")
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

    result = add_entries_query(entries=[test_entry, internal_entry], client=client)

    result = get_entries_query(session_id=session_id, client=client)

    assert len(result["entry_id"]) == 1


@test("model: naive context window")
def _():
    client = cozo_client()
    session_id = uuid4()

    test_entry = Entry(
        session_id=session_id,
        role="user",
        content="test entry content",
    )

    result = add_entries_query(
        entries=[test_entry],
        client=client,
    )

    result = naive_context_window_query(session_id=session_id, client=client)

    assert len(result["created_at"]) == 1


@test("model: procedural memory context")
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

    [
        add_entries_query(entries=[test_entry], client=client),
        create_user_query(
            user_id=user_id,
            developer_id=developer_id,
            name="test user",
            about="test user about",
            client=client,
        ),
        create_agent_query(
            agent_id=agent_id,
            model=MODEL,
            developer_id=developer_id,
            name="test agent",
            about="test agent about",
            instructions=[test_instruction1, test_instruction2],
            client=client,
        ),
        create_session_query(
            developer_id=developer_id,
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            situation="test situation",
            client=client,
        ),
        create_function_query(
            agent_id=agent_id, id=tool_id, function=test_function, client=client
        ),
        create_docs_query(
            owner_type="agent",
            owner_id=agent_id,
            id=agent_doc_id,
            title=test_agent_doc,
            content=test_agent_doc,
            client=client,
        ),
        create_docs_query(
            owner_type="user",
            owner_id=user_id,
            id=user_doc_id,
            title=test_user_doc,
            content=test_user_doc,
            client=client,
        ),
        embed_functions_query(
            agent_id=agent_id,
            tool_ids=[tool_id],
            embeddings=[[1.0] * 768],
            client=client,
        ),
        embed_docs_snippets_query(
            agent_doc_id, snippet_indices=[0], embeddings=[[1.0] * 768], client=client
        ),
        embed_docs_snippets_query(
            user_doc_id, snippet_indices=[0], embeddings=[[1.0] * 768], client=client
        ),
    ]

    # Run the query
    result = proc_mem_context_query(
        session_id=session_id,
        tool_query_embedding=[0.9] * 768,
        doc_query_embedding=[0.9] * 768,
        client=client,
    )

    assert len(result) == 8
