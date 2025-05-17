from uuid import uuid4

from agents_api.autogen.openapi_model import CreateDocRequest, Doc
from agents_api.clients.pg import create_db_pool
from agents_api.queries.docs.create_doc import create_doc
from agents_api.queries.docs.delete_doc import delete_doc
from agents_api.queries.docs.get_doc import get_doc
from agents_api.queries.docs.list_docs import list_docs
from agents_api.queries.docs.search_docs_by_embedding import search_docs_by_embedding
from agents_api.queries.docs.search_docs_by_text import search_docs_by_text
from agents_api.queries.docs.search_docs_hybrid import search_docs_hybrid
from fastapi import HTTPException
import pytest

from .fixtures import (
    pg_dsn,
    test_agent,
    test_developer,
    test_doc,
    test_doc_with_embedding,
    test_user,
)

EMBEDDING_SIZE: int = 1024


@pytest.mark.asyncio
async def test_query_create_user_doc(dsn=pg_dsn, developer=test_developer, user=test_user):
    """query: create user doc"""
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

    assert isinstance(doc_created, Doc)
    assert doc_created.id is not None

    # Verify doc appears in user's docs
    found = await get_doc(
        developer_id=developer.id,
        doc_id=doc_created.id,
        connection_pool=pool,
    )
    assert found.id == doc_created.id


@pytest.mark.asyncio
async def test_query_create_user_doc_user_not_found(dsn=pg_dsn, developer=test_developer):
    """query: create user doc, user not found"""
    pool = await create_db_pool(dsn=dsn)
    with pytest.pytest.raises(HTTPException) as e:
        await create_doc(
            developer_id=developer.id,
            data=CreateDocRequest(
                title="User Doc",
                content=["Docs for user testing", "Docs for user testing 2"],
                metadata={"test": "test"},
                embed_instruction="Embed the document",
            ),
            owner_type="user",
            owner_id=uuid4(),
            connection_pool=pool,
        )

    assert e.raised.status_code == 409
    assert e.raised.detail == "Reference to user not found during create"


@pytest.mark.asyncio
async def test_query_create_agent_doc(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    """query: create agent doc"""
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
    assert isinstance(doc, Doc)
    assert doc.id is not None

    # Verify doc appears in agent's docs
    docs_list = await list_docs(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )
    assert any(d.id == doc.id for d in docs_list)


@pytest.mark.asyncio
async def test_query_create_agent_doc_agent_not_found(dsn=pg_dsn, developer=test_developer):
    """query: create agent doc, agent not found"""
    agent_id = uuid4()
    pool = await create_db_pool(dsn=dsn)
    with pytest.pytest.raises(HTTPException) as e:
        await create_doc(
            developer_id=developer.id,
            data=CreateDocRequest(
                title="Agent Doc",
                content="Docs for agent testing",
                metadata={"test": "test"},
                embed_instruction="Embed the document",
            ),
            owner_type="agent",
            owner_id=agent_id,
            connection_pool=pool,
        )

    assert e.raised.status_code == 409
    assert e.raised.detail == "Reference to agent not found during create"


@pytest.mark.asyncio
async def test_query_get_doc(dsn=pg_dsn, developer=test_developer, doc=test_doc):
    """query: get doc"""
    pool = await create_db_pool(dsn=dsn)
    doc_test = await get_doc(
        developer_id=developer.id,
        doc_id=doc.id,
        connection_pool=pool,
    )
    assert isinstance(doc_test, Doc)
    assert doc_test.id == doc.id
    assert doc_test.title is not None
    assert doc_test.content is not None


@pytest.mark.asyncio
async def test_query_list_user_docs(dsn=pg_dsn, developer=test_developer, user=test_user):
    """query: list user docs"""
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
    assert any(d.id == doc_user.id for d in docs_list)

    # Create a doc with a different metadata
    doc_user_different_metadata = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="User List Test 2",
            content="Some user doc content 2",
            metadata={"test": "test2"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
    )

    docs_list_metadata = await list_docs(
        developer_id=developer.id,
        owner_type="user",
        owner_id=user.id,
        connection_pool=pool,
        metadata_filter={"test": "test2"},
    )
    assert len(docs_list_metadata) >= 1
    assert any(d.id == doc_user_different_metadata.id for d in docs_list_metadata)
    assert any(d.metadata == {"test": "test2"} for d in docs_list_metadata)


@pytest.mark.asyncio
async def test_query_list_user_docs_invalid_limit(dsn=pg_dsn, developer=test_developer, user=test_user):
    """query: list user docs, invalid limit"""
    pool = await create_db_pool(dsn=dsn)

    await create_doc(
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

    with pytest.pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=developer.id,
            owner_type="user",
            owner_id=user.id,
            connection_pool=pool,
            limit=101,
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"


@pytest.mark.asyncio
async def test_query_list_user_docs_invalid_offset(dsn=pg_dsn, developer=test_developer, user=test_user):
    """query: list user docs, invalid offset"""
    pool = await create_db_pool(dsn=dsn)

    await create_doc(
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

    with pytest.pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=developer.id,
            owner_type="user",
            owner_id=user.id,
            connection_pool=pool,
            offset=-1,
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Offset must be >= 0"


@pytest.mark.asyncio
async def test_query_list_user_docs_invalid_sort_by(dsn=pg_dsn, developer=test_developer, user=test_user):
    """query: list user docs, invalid sort by"""
    pool = await create_db_pool(dsn=dsn)

    await create_doc(
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

    with pytest.pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=developer.id,
            owner_type="user",
            owner_id=user.id,
            connection_pool=pool,
            sort_by="invalid",
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort field"


@pytest.mark.asyncio
async def test_query_list_user_docs_invalid_sort_direction(dsn=pg_dsn, developer=test_developer, user=test_user):
    """query: list user docs, invalid sort direction"""
    pool = await create_db_pool(dsn=dsn)

    await create_doc(
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

    with pytest.pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=developer.id,
            owner_type="user",
            owner_id=user.id,
            connection_pool=pool,
            direction="invalid",
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort direction"


@pytest.mark.asyncio
async def test_query_list_agent_docs(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    """query: list agent docs"""
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

    # Create a doc with a different metadata
    doc_agent_different_metadata = await create_doc(
        developer_id=developer.id,
        data=CreateDocRequest(
            title="Agent List Test 2",
            content="Some agent doc content 2",
            metadata={"test": "test2"},
            embed_instruction="Embed the document",
        ),
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
    )

    # List agent's docs
    docs_list_metadata = await list_docs(
        developer_id=developer.id,
        owner_type="agent",
        owner_id=agent.id,
        connection_pool=pool,
        metadata_filter={"test": "test2"},
    )
    assert len(docs_list_metadata) >= 1
    assert any(d.id == doc_agent_different_metadata.id for d in docs_list_metadata)
    assert any(d.metadata == {"test": "test2"} for d in docs_list_metadata)


@pytest.mark.asyncio
async def test_query_list_agent_docs_invalid_limit(dsn=pg_dsn):
    """query: list agent docs, invalid limit"""
    """Test that listing agent docs with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=uuid4(),
            owner_type="agent",
            owner_id=uuid4(),
            connection_pool=pool,
            limit=101,
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"


@pytest.mark.asyncio
async def test_query_list_agent_docs_invalid_offset(dsn=pg_dsn):
    """query: list agent docs, invalid offset"""
    """Test that listing agent docs with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=uuid4(),
            owner_type="agent",
            owner_id=uuid4(),
            connection_pool=pool,
            offset=-1,
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Offset must be >= 0"


@pytest.mark.asyncio
async def test_query_list_agent_docs_invalid_sort_by(dsn=pg_dsn):
    """query: list agent docs, invalid sort by"""
    """Test that listing agent docs with an invalid sort by raises an exception."""
    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=uuid4(),
            owner_type="agent",
            owner_id=uuid4(),
            connection_pool=pool,
            sort_by="invalid",
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort field"


@pytest.mark.asyncio
async def test_query_list_agent_docs_invalid_sort_direction(dsn=pg_dsn):
    """query: list agent docs, invalid sort direction"""
    """Test that listing agent docs with an invalid sort direction raises an exception."""
    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=uuid4(),
            owner_type="agent",
            owner_id=uuid4(),
            connection_pool=pool,
            direction="invalid",
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort direction"


@pytest.mark.asyncio
async def test_query_delete_user_doc(dsn=pg_dsn, developer=test_developer, user=test_user):
    """query: delete user doc"""
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


@pytest.mark.asyncio
async def test_query_delete_agent_doc(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    """query: delete agent doc"""
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


@pytest.mark.asyncio
async def test_query_search_docs_by_text(dsn=pg_dsn, agent=test_agent, developer=test_developer):
    """query: search docs by text"""
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


@pytest.mark.asyncio
async def test_query_search_docs_by_text_with_technical_terms_and_phrases(dsn=pg_dsn, developer=test_developer, agent=test_agent):
    """query: search docs by text with technical terms and phrases"""
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
            trigram_similarity_threshold=0.4,
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


@pytest.mark.asyncio
async def test_query_search_docs_by_embedding(
    """query: search docs by embedding"""
    dsn=pg_dsn,
    agent=test_agent,
    developer=test_developer,
    doc=test_doc_with_embedding,
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


@pytest.mark.asyncio
async def test_query_search_docs_by_hybrid(
    """query: search docs by hybrid"""
    dsn=pg_dsn,
    agent=test_agent,
    developer=test_developer,
    doc=test_doc_with_embedding,
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
        trigram_similarity_threshold=0.4,
        k_multiplier=7,
        connection_pool=pool,
    )

    assert len(result) >= 1
    assert result[0].metadata is not None


def test_query_search_docs_by_embedding_with_different_confidence_levels(
    """query: search docs by embedding with different confidence levels"""
#     dsn=pg_dsn, agent=test_agent, developer=test_developer, doc=test_doc_with_embedding
# ):
#     pool = await create_db_pool(dsn=dsn)

#     # Get query embedding (using original doc's embedding)
#     query_embedding = make_vector_with_similarity(EMBEDDING_SIZE, 0.7)

#     # Test with different confidence levels
#     confidence_tests = [
#         (0.99, 0),  # Very high similarity threshold - should find no results
#         (0.7, 1),  # High similarity - should find 1 result (the embedding with all 1.0s)
#         (0.3, 2),  # Medium similarity - should find 2 results (including 0.3-0.7 embedding)
#         (-0.8, 3),  # Low similarity - should find 3 results (including -0.8 to 0.8 embedding)
#         (-1.0, 4),  # Lowest similarity - should find all 4 results (including alternating -1/1)
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
