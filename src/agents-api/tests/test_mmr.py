from uuid import UUID

import numpy as np
from agents_api.autogen.Docs import DocOwner, DocReference, Snippet
from agents_api.common.utils.mmr import apply_mmr_to_docs
from ward import test


def create_test_doc(doc_id, embedding=None):
    """Helper function to create test document references"""

    return DocReference(
        id=UUID(doc_id) if isinstance(doc_id, str) else doc_id,
        owner=DocOwner(id=UUID("00000000-0000-0000-0000-000000000000"), role="agent"),
        snippet=Snippet(
            index=0,
            content=f"Test content {doc_id}",
            embedding=embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
        ),
        metadata={},
    )


@test("utility: test to apply_mmr_to_docs")
def _():
    # Create test documents with embeddings
    docs = [
        create_test_doc("550e8400-e29b-41d4-a716-446655440000", np.array([0.1, 0.2, 0.3])),
        create_test_doc("6ba7b810-9dad-11d1-80b4-00c04fd430c8", np.array([0.2, 0.3, 0.4])),
        create_test_doc("6ba7b811-9dad-11d1-80b4-00c04fd430c8", np.array([0.3, 0.4, 0.5])),
        create_test_doc("6ba7b812-9dad-11d1-80b4-00c04fd430c8", np.array([0.4, 0.5, 0.6])),
        create_test_doc("6ba7b813-9dad-11d1-80b4-00c04fd430c8", np.array([0.5, 0.6, 0.7])),
        create_test_doc("6ba7b814-9dad-11d1-80b4-00c04fd430c8", None),  # Doc without embedding
    ]

    query_embedding = np.array([0.3, 0.3, 0.3])

    # Test with MMR strength = 0.0
    result = apply_mmr_to_docs(docs, query_embedding, limit=3, mmr_strength=0.0)
    assert len(result) == 3

    # Test with not enough docs with embeddings (only 1, minimum required is 2 for MMR to work)
    docs_few_embeddings = [
        create_test_doc("550e8400-e29b-41d4-a716-446655440000", np.array([0.1, 0.2, 0.3])),
        create_test_doc("6ba7b810-9dad-11d1-80b4-00c04fd430c8", None),
        create_test_doc("550e8400-e29b-41d4-a716-446655441122", np.array([0.11, 0.21, 0.31])),
        create_test_doc("6ba7b811-9dad-11d1-80b4-00c04fd430c8", None),
    ]

    # Will return the top k docs irrespective of MMR strength and presence of embeddings
    result = apply_mmr_to_docs(docs_few_embeddings, query_embedding, limit=2, mmr_strength=0.5)
    assert len(result) == 2  # Should only return docs with embeddings
    assert result[0].id == UUID("550e8400-e29b-41d4-a716-446655441122")
    assert result[1].id == UUID("550e8400-e29b-41d4-a716-446655440000")

    # Test with limit greater than available docs
    result = apply_mmr_to_docs(docs, query_embedding, limit=10, mmr_strength=0.5)
    assert len(result) == 5  # Only 5 docs have embeddings


@test("utility: test mmr with different mmr_strength values")
def _():
    # Create test documents with embeddings
    docs = [
        create_test_doc(
            UUID("550e8400-e29b-41d4-a716-446655440001"), np.array([0.9, 0.1, 0.1])
        ),  # Most similar to query
        create_test_doc(
            UUID("550e8400-e29b-41d4-a716-446655440002"), np.array([0.8, 0.1, 0.1])
        ),  # Second most similar
        create_test_doc(
            UUID("550e8400-e29b-41d4-a716-446655440003"), np.array([0.7, 0.1, 0.1])
        ),  # Third most similar
        create_test_doc(
            UUID("550e8400-e29b-41d4-a716-446655440004"), np.array([0.1, 0.9, 0.1])
        ),  # Very different from others
        create_test_doc(
            UUID("550e8400-e29b-41d4-a716-446655440005"), np.array([0.1, 0.1, 0.9])
        ),  # Very different from others
    ]

    query_embedding = np.array([1.0, 0.0, 0.0])

    # With mmr_strength = 0, should return docs in order of similarity to query
    result_relevance = apply_mmr_to_docs(docs, query_embedding, limit=3, mmr_strength=0.0)
    assert len(result_relevance) == 3
    assert result_relevance[0].id == UUID("550e8400-e29b-41d4-a716-446655440001")
    assert result_relevance[1].id == UUID("550e8400-e29b-41d4-a716-446655440002")
    assert result_relevance[2].id == UUID("550e8400-e29b-41d4-a716-446655440003")

    # With mmr_strength = 1, should prioritize diversity
    result_diverse = apply_mmr_to_docs(docs, query_embedding, limit=3, mmr_strength=1.0)
    assert len(result_diverse) == 3
    # The first document should still be the most relevant one
    assert result_diverse[0].id == UUID("550e8400-e29b-41d4-a716-446655440001")
    # But the next ones should be diverse
    assert UUID("550e8400-e29b-41d4-a716-446655440004") in [doc.id for doc in result_diverse]
    assert UUID("550e8400-e29b-41d4-a716-446655440005") in [doc.id for doc in result_diverse]


@test("utility: test mmr with empty docs list")
def _():
    query_embedding = np.array([0.3, 0.3, 0.3])

    # Test with empty docs list
    result = apply_mmr_to_docs([], query_embedding, limit=3, mmr_strength=0.5)
    assert len(result) == 0

    # Test with all docs having no embeddings
    docs_no_embeddings = [
        create_test_doc(UUID("550e8400-e29b-41d4-a716-446655440001"), None),
        create_test_doc(UUID("550e8400-e29b-41d4-a716-446655440002"), None),
        create_test_doc(UUID("550e8400-e29b-41d4-a716-446655440003"), None),
    ]

    # Will return the top limit docs without MMR since no embeddings are present
    result = apply_mmr_to_docs(docs_no_embeddings, query_embedding, limit=1, mmr_strength=0.5)
    assert len(result) == 1
