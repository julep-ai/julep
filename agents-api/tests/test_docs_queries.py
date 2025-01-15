from agents_api.autogen.openapi_model import CreateDocRequest
from agents_api.clients.pg import create_db_pool
from agents_api.common.nlp import text_to_tsvector_query
from agents_api.queries.docs.create_doc import create_doc
from agents_api.queries.docs.delete_doc import delete_doc
from agents_api.queries.docs.get_doc import get_doc
from agents_api.queries.docs.list_docs import list_docs
from agents_api.queries.docs.search_docs_by_embedding import search_docs_by_embedding
from agents_api.queries.docs.search_docs_by_text import search_docs_by_text
from agents_api.queries.docs.search_docs_hybrid import search_docs_hybrid
from ward import test

from .fixtures import (
    pg_dsn,
    test_agent,
    test_developer,
    test_doc,
    test_doc_with_embedding,
    test_user,
)

EMBEDDING_SIZE: int = 1024


@test("query: create user doc")
async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
    pool = await create_db_pool(dsn=dsn)
    doc_created = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="User Doc",
            content=["Docs for user testing", "Docs for user testing 2"],
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )

    assert doc_created.id is not None

    # Verify doc appears in user's docs
    found = await get_doc(
        developer_id=developer.id,
        doc_id=doc_created.id,
        connection_pool=pool,
    )
    assert found.id == doc_created.id


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
    assert doc.id is not None

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
    assert doc_test.title is not None
    assert doc_test.content is not None


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
    doc = await create_doc(
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

    # Search using simpler terms first
    result = await search_docs_by_text(
        developer_id=developer.id,
        owners=[("agent", agent.id)],
        query="world",
        k=3,
        search_language="english",
        metadata_filter={"test": "test"},
        connection_pool=pool,
    )

    print("\nSearch results:", result)

    # More specific assertions
    assert len(result) >= 1, "Should find at least one document"
    assert any(d.id == doc.id for d in result), f"Should find document {doc.id}"
    assert result[0].metadata == {"test": "test"}, "Metadata should match"


@test("query: search docs by text with technical terms and phrases")
async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)

    # Create documents with technical content
    doc1 = await create_doc(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        data=CreateDocRequest(
            title="Technical Document",
            content="API endpoints using REST architecture with JSON payloads",
            metadata={"domain": "technical"},
            embed_instruction="Embed the document",
        ),
        connection_pool=pool,
    )

    doc2 = await create_doc(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        data=CreateDocRequest(
            title="More Technical Terms",
            content="Database optimization using indexing and query planning",
            metadata={"domain": "technical"},
            embed_instruction="Embed the document",
        ),
        connection_pool=pool,
    )

    # Test with technical terms
    technical_queries = [
        "API endpoints",
        "REST architecture",
        "database optimization",
        "indexing",
    ]

    for query in technical_queries:
        results = await search_docs_by_text(
            developer_id=developer.id,
            owners=[("agent", agent.id)],
            query=query,
            k=3,
            search_language="english",
            connection_pool=pool,
        )

        print(f"\nSearch results for '{query}':", results)

        # Verify appropriate document is found based on query
        if "API" in query or "REST" in query:
            assert any(doc.id == doc1.id for doc in results), (
                f"Doc1 should be found with query '{query}'"
            )
        if "database" in query.lower() or "indexing" in query:
            assert any(doc.id == doc2.id for doc in results), (
                f"Doc2 should be found with query '{query}'"
            )


@test("query: search docs by embedding")
async def _(
    dsn=pg_dsn, agent=test_agent, developer=test_developer, doc=test_doc_with_embedding
):
    pool = await create_db_pool(dsn=dsn)

    assert doc.embeddings is not None

    # Get query embedding by averaging the embeddings (list of floats)
    query_embedding = [sum(k) / len(k) for k in zip(*doc.embeddings)]

    # Search using the correct parameter types
    result = await search_docs_by_embedding(
        developer_id=developer.id,
        owners=[("agent", agent.id)],
        embedding=query_embedding,
        k=3,  # Add k parameter
        metadata_filter={"test": "test"},  # Add metadata filter
        connection_pool=pool,
    )

    assert len(result) >= 1
    assert result[0].metadata is not None


@test("query: search docs by hybrid")
async def _(
    dsn=pg_dsn, agent=test_agent, developer=test_developer, doc=test_doc_with_embedding
):
    pool = await create_db_pool(dsn=dsn)

    # Get query embedding by averaging the embeddings (list of floats)
    query_embedding = [sum(k) / len(k) for k in zip(*doc.embeddings)]

    # Search using the correct parameter types
    result = await search_docs_hybrid(
        developer_id=developer.id,
        owners=[("agent", agent.id)],
        text_query=doc.content[0] if isinstance(doc.content, list) else doc.content,
        embedding=query_embedding,
        k=3,  # Add k parameter
        metadata_filter={"test": "test"},  # Add metadata filter
        connection_pool=pool,
    )

    assert len(result) >= 1
    assert result[0].metadata is not None


# @test("query: search docs by embedding with different confidence levels")
# async def _(
#     dsn=pg_dsn, agent=test_agent, developer=test_developer, doc=test_doc_with_embedding
# ):
#     pool = await create_db_pool(dsn=dsn)

#     # Get query embedding (using original doc's embedding)
#     query_embedding = make_vector_with_similarity(EMBEDDING_SIZE, 0.7)

#     # Test with different confidence levels
#     confidence_tests = [
#         (0.99, 0),  # Very high similarity threshold - should find no results
#         (0.7, 1),   # High similarity - should find 1 result (the embedding with all 1.0s)
#         (0.3, 2),   # Medium similarity - should find 2 results (including 0.3-0.7 embedding)
#         (-0.8, 3),  # Low similarity - should find 3 results (including -0.8 to 0.8 embedding)
#         (-1.0, 4)   # Lowest similarity - should find all 4 results (including alternating -1/1)
#     ]

#     for confidence, expected_min_results in confidence_tests:
#         results = await search_docs_by_embedding(
#             developer_id=developer.id,
#             owners=[("agent", agent.id)],
#             embedding=query_embedding,
#             k=3,
#             confidence=confidence,
#             metadata_filter={"test": "test"},
#             connection_pool=pool,
#         )

#         print(f"\nSearch results with confidence {confidence}:")
#         for r in results:
#             print(f"- Doc ID: {r.id}, Distance: {r.distance}")

#         assert len(results) >= expected_min_results, (
#             f"Expected at least {expected_min_results} results with confidence {confidence}, got {len(results)}"
#         )

#         if results:
#             # Verify that all returned results meet the confidence threshold
#             for result in results:
#                 assert result.distance >= confidence, (
#                     f"Result distance {result.distance} is below confidence threshold {confidence}"
#                 )
