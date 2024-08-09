"""
This module contains tests for entry queries against the CozoDB database.
It verifies the functionality of adding, retrieving, and processing entries as defined in the schema.
"""

# Tests for entry queries
from uuid import uuid4

from cozo_migrate.api import apply, init
from pycozo import Client
from ward import test

from agents_api.autogen.Entries import (
    CreateEntriesRequest,
    GetHistoryRequest,
    ListEntriesRequest,
)
from agents_api.autogen.openapi_model import Entry, FunctionDef
from agents_api.models.agent.create_agent import create_agent
from agents_api.models.docs.create_doc import create_doc
from agents_api.models.docs.embed_snippets import embed_snippets
from agents_api.models.entry.create_entries import create_entries
from agents_api.models.entry.get_history import get_history
from agents_api.models.entry.list_entries import list_entries
from agents_api.models.session.create_session import create_session
from agents_api.models.tools.create_tools import create_tools
from agents_api.models.user.create_user import create_user

MODEL = "julep-ai/samantha-1-turbo"


# Initializes a new CozoDB client for testing, applying all migrations.
def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("model: create entry")
def _():
    """
    Tests the addition of a new entry to the database.
    Verifies that the entry can be successfully added using the create_entries function.
    """
    client = cozo_client()
    session_id = uuid4()
    developer_id = uuid4()

    test_entry = Entry(
        session_id=session_id,
        role="user",
        content="test entry content",
    )

    create_entries(
        developer_id=developer_id,
        session_id=session_id,
        data=CreateEntriesRequest(entries=[test_entry]),
        client=client,
    )


@test("model: get entries")
def _():
    """
    Tests the retrieval of entries from the database.
    Verifies that entries matching specific criteria can be successfully retrieved.
    """
    client = cozo_client()
    session_id = uuid4()
    developer_id = uuid4()

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

    create_entries(
        developer_id=developer_id,
        session_id=session_id,
        data=CreateEntriesRequest(entries=[test_entry, internal_entry]),
        client=client,
    )

    result = list_entries(
        developer_id=developer_id,
        session_id=session_id,
        data=ListEntriesRequest(),
        client=client,
    )

    # Asserts that only one entry is retrieved, matching the session_id.
    assert len(result["id"]) == 1


@test("model: procedural memory context")
def _():
    """
    Tests the procedural memory context in the database.
    Verifies the functionality of retrieving relevant memory context based on embeddings.
    """
    client = cozo_client()
    developer_id = uuid4()
    user_id = uuid4()
    agent_id = uuid4()
    session_id = uuid4()
    uuid4()
    user_doc_id = uuid4()
    agent_doc_id = uuid4()

    # Setup: Creates a user, agent, session, function, and documents, then embeds tools and document snippets.
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
        create_entries(
            developer_id=developer_id,
            session_id=session_id,
            data=CreateEntriesRequest(entries=[test_entry]),
            client=client,
        ),
        create_user(
            developer_id=developer_id,
            user_id=user_id,
            data={
                "name": "test user",
                "about": "test user about",
            },
            client=client,
        ),
        create_agent(
            developer_id=developer_id,
            agent_id=agent_id,
            data={
                "model": MODEL,
                "name": "test agent",
                "about": "test agent about",
                "instructions": [test_instruction1, test_instruction2],
            },
            client=client,
        ),
        create_session(
            developer_id=developer_id,
            session_id=session_id,
            data={
                "users": [user_id],
                "agents": [agent_id],
                "situation": "test situation",
            },
            client=client,
        ),
        create_tools(
            developer_id=developer_id,
            agent_id=agent_id,
            data=[
                {
                    "name": test_function.name,
                    "description": test_function.description,
                    "parameters": test_function.parameters,
                }
            ],
            client=client,
        ),
        create_doc(
            developer_id=developer_id,
            owner_type="agent",
            owner_id=agent_id,
            doc_id=agent_doc_id,
            data={
                "title": test_agent_doc,
                "content": [test_agent_doc],
            },
            client=client,
        ),
        create_doc(
            developer_id=developer_id,
            owner_type="user",
            owner_id=user_id,
            doc_id=user_doc_id,
            data={
                "title": test_user_doc,
                "content": [test_user_doc],
            },
            client=client,
        ),
        embed_snippets(
            developer_id=developer_id,
            doc_id=agent_doc_id,
            snippet_indices=[0],
            embeddings=[[1.0] * 1024],
            client=client,
        ),
        embed_snippets(
            developer_id=developer_id,
            doc_id=user_doc_id,
            snippet_indices=[0],
            embeddings=[[1.0] * 1024],
            client=client,
        ),
    ]

    # Executes the procedural memory context query to retrieve relevant memory context based on embeddings.
    # Run the query
    result = get_history(
        developer_id=developer_id,
        session_id=session_id,
        data=GetHistoryRequest(),
        client=client,
    )

    assert len(result["entries"]) == 1
