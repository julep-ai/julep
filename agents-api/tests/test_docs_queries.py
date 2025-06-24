from uuid import uuid4

import pytest
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

from .utils import make_vector_with_similarity

# Fixtures are now defined in conftest.py and automatically available to tests

EMBEDDING_SIZE: int = 1024


async def test_query_create_user_doc(pg_dsn, test_developer, test_user):
    pool = await create_db_pool(dsn=pg_dsn)
    doc_created = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="User Doc",
            content=["Docs for user testing", "Docs for user testing 2"],
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    assert isinstance(doc_created, Doc)
    assert doc_created.id is not None

    # Verify doc appears in user's docs
    found = await get_doc(
        developer_id=test_developer.id,
        doc_id=doc_created.id,
        connection_pool=pool,
    )
    assert found.id == doc_created.id


async def test_query_create_user_doc_user_not_found(pg_dsn, test_developer):
    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as e:
        await create_doc(
            developer_id=test_developer.id,
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

    assert e.value.status_code == 409
    assert e.value.detail == "Reference to user not found during create"


async def test_query_create_agent_doc(pg_dsn, test_developer, test_agent):
    pool = await create_db_pool(dsn=pg_dsn)
    doc = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Agent Doc",
            content="Docs for agent testing",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )
    assert isinstance(doc, Doc)
    assert doc.id is not None

    # Verify doc appears in agent's docs
    docs_list = await list_docs(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )
    assert any(d.id == doc.id for d in docs_list)


async def test_query_create_agent_doc_agent_not_found(pg_dsn, test_developer):
    agent_id = uuid4()
    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as e:
        await create_doc(
            developer_id=test_developer.id,
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

    assert e.value.status_code == 409
    assert e.value.detail == "Reference to agent not found during create"


async def test_query_get_doc(pg_dsn, test_developer, test_doc):
    pool = await create_db_pool(dsn=pg_dsn)
    doc_test = await get_doc(
        developer_id=test_developer.id,
        doc_id=test_doc.id,
        connection_pool=pool,
    )
    assert isinstance(doc_test, Doc)
    assert doc_test.id == test_doc.id
    assert doc_test.title is not None
    assert doc_test.content is not None


async def test_query_list_user_docs(pg_dsn, test_developer, test_user):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a doc owned by the user
    doc_user = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="User List Test",
            content="Some user doc content",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    # List user's docs
    docs_list = await list_docs(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )
    assert len(docs_list) >= 1
    assert any(d.id == doc_user.id for d in docs_list)
    assert any(d.id == doc_user.id for d in docs_list)

    # Create a doc with a different metadata
    doc_user_different_metadata = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="User List Test 2",
            content="Some user doc content 2",
            metadata={"test": "test2"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    docs_list_metadata = await list_docs(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
        metadata_filter={"test": "test2"},
    )
    assert len(docs_list_metadata) >= 1
    assert any(d.id == doc_user_different_metadata.id for d in docs_list_metadata)
    assert any(d.metadata == {"test": "test2"} for d in docs_list_metadata)


async def test_query_list_user_docs_invalid_limit(pg_dsn, test_developer, test_user):
    pool = await create_db_pool(dsn=pg_dsn)

    await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="User List Test",
            content="Some user doc content",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    with pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=test_developer.id,
            owner_type="user",
            owner_id=test_user.id,
            connection_pool=pool,
            limit=101,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Limit must be between 1 and 100"


async def test_query_list_user_docs_invalid_offset(pg_dsn, test_developer, test_user):
    pool = await create_db_pool(dsn=pg_dsn)

    await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="User List Test",
            content="Some user doc content",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    with pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=test_developer.id,
            owner_type="user",
            owner_id=test_user.id,
            connection_pool=pool,
            offset=-1,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Offset must be >= 0"


async def test_query_list_user_docs_invalid_sort_by(pg_dsn, test_developer, test_user):
    pool = await create_db_pool(dsn=pg_dsn)

    await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="User List Test",
            content="Some user doc content",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    with pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=test_developer.id,
            owner_type="user",
            owner_id=test_user.id,
            connection_pool=pool,
            sort_by="invalid",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort field"


async def test_query_list_user_docs_invalid_sort_direction(
    pg_dsn, test_developer, test_user
):
    pool = await create_db_pool(dsn=pg_dsn)

    await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="User List Test",
            content="Some user doc content",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    with pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=test_developer.id,
            owner_type="user",
            owner_id=test_user.id,
            connection_pool=pool,
            direction="invalid",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort direction"


async def test_query_list_agent_docs(pg_dsn, test_developer, test_agent):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a doc owned by the agent
    doc_agent = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Agent List Test",
            content="Some agent doc content",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # List agent's docs
    docs_list = await list_docs(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    assert len(docs_list) >= 1
    assert any(d.id == doc_agent.id for d in docs_list)

    # Create a doc with a different metadata
    doc_agent_different_metadata = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Agent List Test 2",
            content="Some agent doc content 2",
            metadata={"test": "test2"},
            embed_instruction="Embed the document",
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # List agent's docs
    docs_list_metadata = await list_docs(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
        metadata_filter={"test": "test2"},
    )
    assert len(docs_list_metadata) >= 1
    assert any(d.id == doc_agent_different_metadata.id for d in docs_list_metadata)
    assert any(d.metadata == {"test": "test2"} for d in docs_list_metadata)


async def test_query_list_agent_docs_invalid_limit(pg_dsn):
    """Test that listing agent docs with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=uuid4(),
            owner_type="agent",
            owner_id=uuid4(),
            connection_pool=pool,
            limit=101,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Limit must be between 1 and 100"


async def test_query_list_agent_docs_invalid_offset(pg_dsn):
    """Test that listing agent docs with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=uuid4(),
            owner_type="agent",
            owner_id=uuid4(),
            connection_pool=pool,
            offset=-1,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Offset must be >= 0"


async def test_query_list_agent_docs_invalid_sort_by(pg_dsn):
    """Test that listing agent docs with an invalid sort by raises an exception."""
    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=uuid4(),
            owner_type="agent",
            owner_id=uuid4(),
            connection_pool=pool,
            sort_by="invalid",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort field"


async def test_query_list_agent_docs_invalid_sort_direction(pg_dsn):
    """Test that listing agent docs with an invalid sort direction raises an exception."""
    pool = await create_db_pool(dsn=pg_dsn)

    with pytest.raises(HTTPException) as exc:
        await list_docs(
            developer_id=uuid4(),
            owner_type="agent",
            owner_id=uuid4(),
            connection_pool=pool,
            direction="invalid",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort direction"


async def test_query_delete_user_doc(pg_dsn, test_developer, test_user):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a doc owned by the user
    doc_user = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="User Delete Test",
            content="Doc for user deletion test",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    # Delete the doc
    await delete_doc(
        developer_id=test_developer.id,
        doc_id=doc_user.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )

    # Verify doc is no longer in user's docs
    docs_list = await list_docs(
        developer_id=test_developer.id,
        owner_type="user",
        owner_id=test_user.id,
        connection_pool=pool,
    )
    assert not any(d.id == doc_user.id for d in docs_list)


async def test_query_delete_agent_doc(pg_dsn, test_developer, test_agent):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a doc owned by the agent
    doc_agent = await create_doc(
        developer_id=test_developer.id,
        data=CreateDocRequest(
            title="Agent Delete Test",
            content="Doc for agent deletion test",
            metadata={"test": "test"},
            embed_instruction="Embed the document",
        ),
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # Delete the doc
    await delete_doc(
        developer_id=test_developer.id,
        doc_id=doc_agent.id,
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )

    # Verify doc is no longer in agent's docs
    docs_list = await list_docs(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        connection_pool=pool,
    )
    assert not any(d.id == doc_agent.id for d in docs_list)


async def test_query_search_docs_by_text(pg_dsn, test_agent, test_developer):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create a test document
    doc = await create_doc(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
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
        developer_id=test_developer.id,
        owners=[("agent", test_agent.id)],
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


async def test_query_search_docs_by_text_with_technical_terms_and_phrases(
    pg_dsn, test_developer, test_agent
):
    pool = await create_db_pool(dsn=pg_dsn)

    # Create documents with technical content
    doc1 = await create_doc(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
        data=CreateDocRequest(
            title="Technical Document",
            content="API endpoints using REST architecture with JSON payloads",
            metadata={"domain": "technical"},
            embed_instruction="Embed the document",
        ),
        connection_pool=pool,
    )

    doc2 = await create_doc(
        developer_id=test_developer.id,
        owner_type="agent",
        owner_id=test_agent.id,
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
            developer_id=test_developer.id,
            owners=[("agent", test_agent.id)],
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


async def test_query_search_docs_by_embedding(
    pg_dsn,
    test_agent,
    test_developer,
    test_doc_with_embedding,
):
    pool = await create_db_pool(dsn=pg_dsn)

    assert test_doc_with_embedding.embeddings is not None

    # Get query embedding by averaging the embeddings (list of floats)
    query_embedding = [
        sum(k) / len(k) for k in zip(*test_doc_with_embedding.embeddings)
    ]

    # Search using the correct parameter types
    result = await search_docs_by_embedding(
        developer_id=test_developer.id,
        owners=[("agent", test_agent.id)],
        embedding=query_embedding,
        k=3,  # Add k parameter
        metadata_filter={"test": "test"},  # Add metadata filter
        connection_pool=pool,
    )

    assert len(result) >= 1
    assert result[0].metadata is not None


async def test_query_search_docs_by_hybrid(
    pg_dsn,
    test_agent,
    test_developer,
    test_doc_with_embedding,
):
    pool = await create_db_pool(dsn=pg_dsn)

    # Get query embedding by averaging the embeddings (list of floats)
    query_embedding = [
        sum(k) / len(k) for k in zip(*test_doc_with_embedding.embeddings)
    ]

    # Search using the correct parameter types
    result = await search_docs_hybrid(
        developer_id=test_developer.id,
        owners=[("agent", test_agent.id)],
        text_query=test_doc_with_embedding.content[0]
        if isinstance(test_doc_with_embedding.content, list)
        else test_doc_with_embedding.content,
        embedding=query_embedding,
        k=3,  # Add k parameter
        metadata_filter={"test": "test"},  # Add metadata filter
        trigram_similarity_threshold=0.4,
        k_multiplier=7,
        connection_pool=pool,
    )

    assert len(result) >= 1
    assert result[0].metadata is not None


async def test_query_search_docs_by_embedding_with_different_confidence_levels(
    pg_dsn, test_agent, test_developer, test_doc_with_embedding
):
    """Test searching docs by embedding with different confidence levels."""
    pool = await create_db_pool(dsn=pg_dsn)

    # AIDEV-NOTE: Debug embedding search issue - verify embeddings are properly stored
    # First, let's verify what embeddings are actually in the database
    # Create a sample vector matching the actual EMBEDDING_SIZE
    sample_vector_str = "[" + ", ".join(["1.0"] * EMBEDDING_SIZE) + "]"
    verify_query = f"""
    SELECT index, chunk_seq,
           substring(embedding::text from 1 for 50) as embedding_preview,
           (embedding <=> $3::vector({EMBEDDING_SIZE})) as sample_distance
    FROM docs_embeddings_store
    WHERE developer_id = $1 AND doc_id = $2
    ORDER BY index
    """
    stored_embeddings = await pool.fetch(
        verify_query, test_developer.id, test_doc_with_embedding.id, sample_vector_str
    )
    print(f"\nStored embeddings for doc {test_doc_with_embedding.id}:")
    for row in stored_embeddings:
        print(
            f"  Index {row['index']}, chunk_seq {row['chunk_seq']}: {row['embedding_preview']}... (sample_distance: {row['sample_distance']})"
        )

    # Get query embedding (using original doc's embedding)
    query_embedding = make_vector_with_similarity(EMBEDDING_SIZE, 0.7)

    # Test with different confidence levels
    # AIDEV-NOTE: search_by_vector returns DISTINCT documents, not individual embeddings
    # Since all embeddings belong to the same document, we'll always get at most 1 result
    # The function returns the best (lowest distance) embedding per document
    confidence_tests = [
        (0.99, 0),  # Very high similarity threshold - should find no results
        (0.7, 1),  # High similarity - should find 1 document
        (0.3, 1),  # Medium similarity - should find 1 document
        (-0.3, 1),  # Low similarity - should find 1 document
        (-0.8, 1),  # Lower similarity - should find 1 document
        (-1.0, 1),  # Lowest similarity - should find 1 document
    ]

    for confidence, expected_min_results in confidence_tests:
        results = await search_docs_by_embedding(
            developer_id=test_developer.id,
            owners=[("agent", test_agent.id)],
            embedding=query_embedding,
            k=10,  # Increase k to ensure we're not limiting results
            confidence=confidence,
            metadata_filter={"test": "test"},
            connection_pool=pool,
        )

        print(
            f"\nSearch results with confidence {confidence} (threshold={1.0 - confidence}):"
        )
        for r in results:
            print(f"- Doc ID: {r.id}, Distance: {r.distance}")

        # For debugging the failing case
        if confidence == 0.3 and len(results) < expected_min_results:
            # Run a manual query to understand what's happening
            debug_query = """
            SELECT doc_id, index,
                   (embedding <=> $1::vector(1024)) as distance
            FROM docs_embeddings
            WHERE developer_id = $2
              AND doc_id IN (SELECT doc_id FROM doc_owners WHERE owner_id = $3 AND owner_type = 'agent')
            ORDER BY distance
            """
            debug_results = await pool.fetch(
                debug_query,
                f"[{', '.join(map(str, query_embedding))}]",
                test_developer.id,
                test_agent.id,
            )
            print(
                f"\nDEBUG: All embeddings with distances for confidence {confidence}:"
            )
            for row in debug_results:
                print(
                    f"  Doc {row['doc_id']}, Index {row['index']}: distance={row['distance']}"
                )

        assert len(results) >= expected_min_results, (
            f"Expected at least {expected_min_results} results with confidence {confidence}, got {len(results)}"
        )

        if results:
            # Verify that all returned results meet the confidence threshold
            # Distance uses cosine distance (0=identical, 2=opposite)
            # The SQL converts confidence to search_threshold = 1.0 - confidence
            # and filters results where distance <= search_threshold
            search_threshold = 1.0 - confidence
            for result in results:
                assert result.distance <= search_threshold, (
                    f"Result distance {result.distance} exceeds search threshold {search_threshold} (confidence={confidence})"
                )
