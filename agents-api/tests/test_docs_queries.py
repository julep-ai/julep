from ward import test

from agents_api.autogen.openapi_model import CreateDocRequest
from agents_api.clients.pg import create_db_pool
from agents_api.queries.docs.create_doc import create_doc
from agents_api.queries.docs.delete_doc import delete_doc
from agents_api.queries.docs.get_doc import get_doc
from agents_api.queries.docs.list_docs import list_docs

# If you wish to test text/embedding/hybrid search, import them:
from agents_api.queries.docs.search_docs_by_text import search_docs_by_text
# from agents_api.queries.docs.search_docs_by_embedding import search_docs_by_embedding
# from agents_api.queries.docs.search_docs_hybrid import search_docs_hybrid
# You can rename or remove these imports to match your actual fixtures
from tests.fixtures import pg_dsn, test_agent, test_developer, test_doc, test_user


@test("query: create user doc")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    pool = await create_db_pool(dsn=dsn)
    doc = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="User Doc",
            content="Docs for user testing",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )
    assert doc.title == "User Doc"

    # Verify doc appears in user's docs
    docs_list = await list_docs(
        developer_id=developer.id,
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )
    assert any(d.id == doc.id for d in docs_list)


@test("query: create agent doc")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)
    doc = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="Agent Doc",
            content="Docs for agent testing",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )
    assert doc.title == "Agent Doc"

    # Verify doc appears in agent's docs
    docs_list = await list_docs(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )
    assert any(d.id == doc.id for d in docs_list)


@test("query: get doc")
async def _(dsn=pg_dsn, developer=test_developer, doc=test_doc):
    pool = await create_db_pool(dsn=dsn)
    doc_test = await get_doc(
        developer_id=developer.id,
        doc_id=doc.id,
        connection_pool=pool,
    )
    assert doc_test.id == doc.id
    assert doc_test.title == doc.title
    assert doc_test.content == doc.content

@test("query: list user docs")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    pool = await create_db_pool(dsn=dsn)

    # Create a doc owned by the user
    doc_user = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="User List Test",
            content="Some user doc content",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )

    # List user's docs
    docs_list = await list_docs(
        developer_id=developer.id,
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )
    assert len(docs_list) >= 1
    assert any(d.id == doc_user.id for d in docs_list)


@test("query: list agent docs")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)

    # Create a doc owned by the agent
    doc_agent = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="Agent List Test",
            content="Some agent doc content",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )

    # List agent's docs
    docs_list = await list_docs(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )
    assert len(docs_list) >= 1
    assert any(d.id == doc_agent.id for d in docs_list)


@test("query: delete user doc")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    pool = await create_db_pool(dsn=dsn)

    # Create a doc owned by the user
    doc_user = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="User Delete Test",
            content="Doc for user deletion test",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )

    # Delete the doc
    await delete_doc(
        developer_id=developer.id,
        doc_id=doc_user.id,
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )

    # Verify doc is no longer in user's docs
    docs_list = await list_docs(
        developer_id=developer.id,
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )
    assert not any(d.id == doc_user.id for d in docs_list)


@test("query: delete agent doc")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)

    # Create a doc owned by the agent
    doc_agent = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="Agent Delete Test",
            content="Doc for agent deletion test",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )

    # Delete the doc
    await delete_doc(
        developer_id=developer.id,
        doc_id=doc_agent.id,
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )

    # Verify doc is no longer in agent's docs
    docs_list = await list_docs(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )
    assert not any(d.id == doc_agent.id for d in docs_list)

@test("query: search docs by text")
async def _(dsn=pg_dsn, agent=test_agent, developer=test_developer):
    pool = await create_db_pool(dsn=dsn)
    
    # Create a test document
    await create_doc(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        data=CreateDocRequest(
            title="Hello", 
            content="The world is a funny little thing",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        connection_pool=pool,
    )

    # Search using the correct parameter types
    result = await search_docs_by_text(
        developer_id=developer.id,
        owners=[("agent", agent.id)],
        query="funny",
        k=3,  # Add k parameter
        search_language="english",  # Add language parameter
        metadata_filter={},  # Add metadata filter
        connection_pool=pool,
    )

    assert len(result) >= 1
    assert result[0].metadata is not None