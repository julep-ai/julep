from agents_api.clients.pg import create_db_pool
from agents_api.queries.docs.search_docs_by_embedding import search_docs_by_embedding
from ward import test

from .fixtures import (
    pg_dsn,
    test_agent,
    test_developer,
    test_doc_with_embedding,
)

EMBEDDING_SIZE: int = 1024


# @test("query: create user doc")
# async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
#     pool = await create_db_pool(dsn=dsn)
#     doc_created = await create_doc(
#         developer_id=developer.id,
#         data=CreateDocRequest(
#             title="User Doc",
#             content=["Docs for user testing", "Docs for user testing 2"],
#             metadata={"test": "test"},
#             embed_instruction="Embed the document",
#         ),
#         owner_type="user",
#         owner_id=user.id,
#         connection_pool=pool,
#     )

#     assert doc_created.id is not None

#     # Verify doc appears in user's docs
#     found = await get_doc(
#         developer_id=developer.id,
#         doc_id=doc_created.id,
#         connection_pool=pool,
#     )
#     assert found.id == doc_created.id


# @test("query: create agent doc")
# async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
#     pool = await create_db_pool(dsn=dsn)
#     doc = await create_doc(
#         developer_id=developer.id,
#         data=CreateDocRequest(
#             title="Agent Doc",
#             content="Docs for agent testing",
#             metadata={"test": "test"},
#             embed_instruction="Embed the document",
#         ),
#         owner_type="agent",
#         owner_id=agent.id,
#         connection_pool=pool,
#     )
#     assert doc.id is not None

#     # Verify doc appears in agent's docs
#     docs_list = await list_docs(
#         developer_id=developer.id,
#         owner_type="agent",
#         owner_id=agent.id,
#         connection_pool=pool,
#     )
#     assert any(d.id == doc.id for d in docs_list)


# @test("query: get doc")
# async def _(dsn=pg_dsn, developer=test_developer, doc=test_doc):
#     pool = await create_db_pool(dsn=dsn)
#     doc_test = await get_doc(
#         developer_id=developer.id,
#         doc_id=doc.id,
#         connection_pool=pool,
#     )
#     assert doc_test.id == doc.id
#     assert doc_test.title is not None
#     assert doc_test.content is not None


# @test("query: list user docs")
# async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
#     pool = await create_db_pool(dsn=dsn)

#     # Create a doc owned by the user
#     doc_user = await create_doc(
#         developer_id=developer.id,
#         data=CreateDocRequest(
#             title="User List Test",
#             content="Some user doc content",
#             metadata={"test": "test"},
#             embed_instruction="Embed the document",
#         ),
#         owner_type="user",
#         owner_id=user.id,
#         connection_pool=pool,
#     )

#     # List user's docs
#     docs_list = await list_docs(
#         developer_id=developer.id,
#         owner_type="user",
#         owner_id=user.id,
#         connection_pool=pool,
#     )
#     assert len(docs_list) >= 1
#     assert any(d.id == doc_user.id for d in docs_list)


# @test("query: list agent docs")
# async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
#     pool = await create_db_pool(dsn=dsn)

#     # Create a doc owned by the agent
#     doc_agent = await create_doc(
#         developer_id=developer.id,
#         data=CreateDocRequest(
#             title="Agent List Test",
#             content="Some agent doc content",
#             metadata={"test": "test"},
#             embed_instruction="Embed the document",
#         ),
#         owner_type="agent",
#         owner_id=agent.id,
#         connection_pool=pool,
#     )

#     # List agent's docs
#     docs_list = await list_docs(
#         developer_id=developer.id,
#         owner_type="agent",
#         owner_id=agent.id,
#         connection_pool=pool,
#     )
#     assert len(docs_list) >= 1
#     assert any(d.id == doc_agent.id for d in docs_list)


# @test("query: delete user doc")
# async def _(dsn=pg_dsn, developer=test_developer, user=test_user):
#     pool = await create_db_pool(dsn=dsn)

#     # Create a doc owned by the user
#     doc_user = await create_doc(
#         developer_id=developer.id,
#         data=CreateDocRequest(
#             title="User Delete Test",
#             content="Doc for user deletion test",
#             metadata={"test": "test"},
#             embed_instruction="Embed the document",
#         ),
#         owner_type="user",
#         owner_id=user.id,
#         connection_pool=pool,
#     )

#     # Delete the doc
#     await delete_doc(
#         developer_id=developer.id,
#         doc_id=doc_user.id,
#         owner_type="user",
#         owner_id=user.id,
#         connection_pool=pool,
#     )

#     # Verify doc is no longer in user's docs
#     docs_list = await list_docs(
#         developer_id=developer.id,
#         owner_type="user",
#         owner_id=user.id,
#         connection_pool=pool,
#     )
#     assert not any(d.id == doc_user.id for d in docs_list)


# @test("query: delete agent doc")
# async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
#     pool = await create_db_pool(dsn=dsn)

#     # Create a doc owned by the agent
#     doc_agent = await create_doc(
#         developer_id=developer.id,
#         data=CreateDocRequest(
#             title="Agent Delete Test",
#             content="Doc for agent deletion test",
#             metadata={"test": "test"},
#             embed_instruction="Embed the document",
#         ),
#         owner_type="agent",
#         owner_id=agent.id,
#         connection_pool=pool,
#     )

#     # Delete the doc
#     await delete_doc(
#         developer_id=developer.id,
#         doc_id=doc_agent.id,
#         owner_type="agent",
#         owner_id=agent.id,
#         connection_pool=pool,
#     )

#     # Verify doc is no longer in agent's docs
#     docs_list = await list_docs(
#         developer_id=developer.id,
#         owner_type="agent",
#         owner_id=agent.id,
#         connection_pool=pool,
#     )
#     assert not any(d.id == doc_agent.id for d in docs_list)


# @test("query: search docs by text")
# async def _(dsn=pg_dsn, agent=test_agent, developer=test_developer):
#     pool = await create_db_pool(dsn=dsn)

#     # Create a test document
#     doc = await create_doc(
#         developer_id=developer.id,
#         owner_type="agent",
#         owner_id=agent.id,
#         data=CreateDocRequest(
#             title="Hello",
#             content="The world is a funny little thing",
#             metadata={"test": "test"},
#             embed_instruction="Embed the document",
#         ),
#         connection_pool=pool,
#     )

#     # Search using simpler terms first
#     result = await search_docs_by_text(
#         developer_id=developer.id,
#         owners=[("agent", agent.id)],
#         query="world",
#         k=3,
#         search_language="english",
#         metadata_filter={"test": "test"},
#         connection_pool=pool,
#     )

#     print("\nSearch results:", result)

#     # More specific assertions
#     assert len(result) >= 1, "Should find at least one document"
#     assert any(d.id == doc.id for d in result), f"Should find document {doc.id}"
#     assert result[0].metadata == {"test": "test"}, "Metadata should match"


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


# @test("query: search docs by hybrid")
# async def _(
#     dsn=pg_dsn, agent=test_agent, developer=test_developer, doc=test_doc_with_embedding
# ):
#     pool = await create_db_pool(dsn=dsn)

#     # Get query embedding by averaging the embeddings (list of floats)
#     query_embedding = [sum(k) / len(k) for k in zip(*doc.embeddings)]

#     # Search using the correct parameter types
#     result = await search_docs_hybrid(
#         developer_id=developer.id,
#         owners=[("agent", agent.id)],
#         text_query=doc.content[0] if isinstance(doc.content, list) else doc.content,
#         embedding=query_embedding,
#         k=3,  # Add k parameter
#         metadata_filter={"test": "test"},  # Add metadata filter
#         connection_pool=pool,
#     )

#     assert len(result) >= 1
#     assert result[0].metadata is not None


# @test("query: test tsvector with technical terms and phrases")
# async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
#     pool = await create_db_pool(dsn=dsn)

#     # Create documents with technical content
#     doc1 = await create_doc(
#         developer_id=developer.id,
#         owner_type="agent",
#         owner_id=agent.id,
#         data=CreateDocRequest(
#             title="Technical Document",
#             content="API endpoints using REST architecture with JSON payloads",
#             metadata={"domain": "technical"},
#             embed_instruction="Embed the document",
#         ),
#         connection_pool=pool,
#     )

#     doc2 = await create_doc(
#         developer_id=developer.id,
#         owner_type="agent",
#         owner_id=agent.id,
#         data=CreateDocRequest(
#             title="More Technical Terms",
#             content="Database optimization using indexing and query planning",
#             metadata={"domain": "technical"},
#             embed_instruction="Embed the document",
#         ),
#         connection_pool=pool,
#     )

#     # Test with technical terms
#     technical_queries = [
#         "API endpoints",
#         "REST architecture",
#         "database optimization",
#         "indexing"
#     ]

#     for query in technical_queries:
#         results = await search_docs_by_text(
#             developer_id=developer.id,
#             owners=[("agent", agent.id)],
#             query=query,
#             k=3,
#             search_language="english",
#             connection_pool=pool,
#         )

#         print(f"\nSearch results for '{query}':", results)

#         # Verify appropriate document is found based on query
#         if "API" in query or "REST" in query:
#             assert any(doc.id == doc1.id for doc in results), f"Doc1 should be found with query '{query}'"
#         if "database" in query.lower() or "indexing" in query:
#             assert any(doc.id == doc2.id for doc in results), f"Doc2 should be found with query '{query}'"

# @test("query: test tsvector with varying content lengths and special characters")
# async def _(dsn=pg_dsn, developer=test_developer, agent=test_agent):
#     pool = await create_db_pool(dsn=dsn)

#     # Create documents with different content lengths
#     short_doc = await create_doc(
#         developer_id=developer.id,
#         owner_type="agent",
#         owner_id=agent.id,
#         data=CreateDocRequest(
#             title="Short",
#             content="Brief test document",
#             metadata={"length": "short"},
#             embed_instruction="Embed the document",
#         ),
#         connection_pool=pool,
#     )

#     medium_doc = await create_doc(
#         developer_id=developer.id,
#         owner_type="agent",
#         owner_id=agent.id,
#         data=CreateDocRequest(
#             title="Medium",
#             content="This is a medium length document that contains more words and context for testing purposes",
#             metadata={"length": "medium"},
#             embed_instruction="Embed the document",
#         ),
#         connection_pool=pool,
#     )

# long_doc = await create_doc(
#     developer_id=developer.id,
#     owner_type="agent",
#     owner_id=agent.id,
#     data=CreateDocRequest(
#         title="Long",
#         content="This is a much longer document that contains multiple sentences. It includes various terms and phrases. \
#         The purpose is to test how the search handles longer content with more context. \
#         It should still be able to find relevant matches based on the search query.",
#         metadata={"length": "long"},
#         embed_instruction="Embed the document",
#     ),
#     connection_pool=pool,
# )

#     special_doc = await create_doc(
#         developer_id=developer.id,
#         owner_type="agent",
#         owner_id=agent.id,
#         data=CreateDocRequest(
#             title="Special Characters",
#             content="Testing! With? Different... punctuation; marks: and-hyphens, plus+signs & ampersands",
#             metadata={"type": "special"},
#             embed_instruction="Embed the document",
#         ),
#         connection_pool=pool,
#     )

#     # Test cases for different content lengths
#     length_test_cases = [
#         ("brief test", short_doc.id),
#         ("medium length document", medium_doc.id),
#         ("multiple sentences", long_doc.id),
#         ("document", None)  # Should find all documents
#     ]

#     for query, expected_doc_id in length_test_cases:
#         results = await search_docs_by_text(
#             developer_id=developer.id,
#             owners=[("agent", agent.id)],
#             query=query,
#             k=3,
#             search_language="english",
#             connection_pool=pool,
#         )

#         print(f"\nSearch results for '{query}':", results)

#         if expected_doc_id:
#             assert any(doc.id == expected_doc_id for doc in results), \
#                 f"Expected document should be found with query '{query}'"
#         else:
#             # For general terms, verify multiple documents are found
#             assert len(results) > 1, f"Multiple documents should be found with query '{query}'"

# @test("query: test direct tsvector generation")
# async def _():
#     test_cases = [
#         # Single words
#         (
#             "test",
#             "'test'"
#         ),
#         (
#             "testing",
#             "'testing'"
#         ),

#         # Multiple words in single sentence
#         (
#             "quick brown fox",
#             "'quick' & 'brown' & 'fox'"
#         ),
#         (
#             "The Quick Brown Fox",
#             "'quick' & 'brown' & 'fox'"
#         ),

#         # Technical terms and phrases
#         (
#             "machine learning algorithm",
#             "('machine' <-> 'learning') & 'algorithm'"
#         ),
#         (
#             "REST API implementation",
#             "'rest' & 'api' & 'implementation'"
#         ),

#         # Multiple sentences
#         (
#             "Machine learning is great. Data science rocks.",
#             "('machine' <-> 'learning') & 'great' | ('data' <-> 'science') & 'rocks'"
#         ),

#         # Quoted phrases
#         (
#             '"quick brown fox"',
#             "('quick' <-> 'brown' <-> 'fox')"
#         ),
#         (
#             'Find "machine learning" algorithms',
#             "('machine' <-> 'learning') & 'algorithms' & 'find'"
#         ),

#         # Multiple quoted phrases
#         (
#             '"data science" and "machine learning"',
#             "('data' <-> 'science') & ('machine' <-> 'learning')"
#         ),

#         # Edge cases
#         (
#             "",
#             ""
#         ),
#         (
#             "the and or",
#             ""
#         ),
#         (
#             "a",
#             ""
#         ),
#         (
#             "X",
#             "'x'"
#         ),

#         # Empty quotes
#         (
#             '""',
#             ""
#         ),
#         (
#             'test "" phrase',
#             "'test' & 'phrase'"
#         ),
#     ]

#     for input_text, expected_output in test_cases:
#         result = text_to_tsvector_query(input_text)
#         print(f"\nInput: '{input_text}'")
#         print(f"Generated tsquery: '{result}'")
#         print(f"Expected: '{expected_output}'")
#         assert result == expected_output, \
#             f"Expected '{expected_output}' but got '{result}' for input '{input_text}'"


@test("query: search docs by embedding with different confidence levels")
async def _(
    dsn=pg_dsn, agent=test_agent, developer=test_developer, doc=test_doc_with_embedding
):
    pool = await create_db_pool(dsn=dsn)

    # Create a test document with a different embedding
    # different_embedding = [0.5] * EMBEDDING_SIZE  # Create different embedding values
    # await pool.execute(
    #     """
    #     INSERT INTO docs_embeddings_store (developer_id, doc_id, index, chunk_seq, chunk, embedding)
    #     VALUES ($1, $2, 0, 1, $3, $4)
    #     """,  # Changed chunk_seq from 0 to 1
    #     developer.id,
    #     doc.id,
    #     "Different test content",
    #     f"[{', '.join([str(x) for x in different_embedding])}]",
    # )

    # Get query embedding (using original doc's embedding)
    query_embedding = [sum(k) / len(k) for k in zip(*doc.embeddings)]

    # Test with different confidence levels
    confidence_tests = [
        (0.99, 0),  # High confidence should find no results
        (0.7, 1),  # Medium confidence should find some results
        (0.5, 2),  # Lower confidence should find more results
        (0.1, 2),  # Very low confidence should find all results
    ]

    for confidence, expected_min_results in confidence_tests:
        results = await search_docs_by_embedding(
            developer_id=developer.id,
            owners=[("agent", agent.id)],
            embedding=query_embedding,
            k=3,
            confidence=confidence,
            metadata_filter={"test": "test"},
            connection_pool=pool,
        )

        print(f"\nSearch results with confidence {confidence}:")
        for r in results:
            print(f"- Doc ID: {r.id}, Distance: {r.distance}")

        assert len(results) >= expected_min_results, (
            f"Expected at least {expected_min_results} results with confidence {confidence}, got {len(results)}"
        )

        if results:
            # Verify that all returned results meet the confidence threshold
            for result in results:
                assert result.distance >= confidence, (
                    f"Result distance {result.distance} is below confidence threshold {confidence}"
                )
