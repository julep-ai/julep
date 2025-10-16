from uuid import uuid4

from agents_api.autogen.Docs import DocOwner, DocReference, Snippet
from agents_api.autogen.openapi_model import (
    HybridDocSearchRequest,
    TextOnlyDocSearchRequest,
    VectorDocSearchRequest,
)
from agents_api.common.utils.get_doc_search import (
    get_language,
    get_search_fn_and_params,
    strip_embeddings,
)
from agents_api.queries.docs.search_docs_by_embedding import search_docs_by_embedding
from agents_api.queries.docs.search_docs_by_text import search_docs_by_text
from agents_api.queries.docs.search_docs_hybrid import search_docs_hybrid
from fastapi import HTTPException
from ward import raises, test


@test("get_language: valid language code returns lowercase language name")
def _():
    result = get_language("en")
    assert result == "english_unaccent"

    result = get_language("fr")
    assert result == "french"


@test("get_language: empty language code raises HTTPException")
def _():
    with raises(HTTPException) as exc:
        get_language("")

    assert exc.raised.status_code == 422
    assert exc.raised.detail == "Invalid ISO 639 language code."


@test("get_search_fn_and_params: text-only search request")
def _():
    request = TextOnlyDocSearchRequest(
        text="search query",
        limit=10,
        lang="en",
        metadata_filter={"field": "value"},
        trigram_similarity_threshold=0.4,
    )

    search_fn, params, post_processing = get_search_fn_and_params(request)

    assert search_fn == search_docs_by_text
    assert params == {
        "query": "search query",
        "k": 10,
        "metadata_filter": {"field": "value"},
        "search_language": "english_unaccent",
        "extract_keywords": False,
        "trigram_similarity_threshold": None,
    }
    assert post_processing == {
        "include_embeddings": True,
    }


@test("get_search_fn_and_params: text-only search request with include_embeddings=False")
def _():
    request = TextOnlyDocSearchRequest(
        text="search query",
        limit=10,
        lang="en",
        metadata_filter={"field": "value"},
        trigram_similarity_threshold=0.4,
        include_embeddings=False,
    )

    search_fn, params, post_processing = get_search_fn_and_params(request)

    assert search_fn == search_docs_by_text
    assert params == {
        "query": "search query",
        "k": 10,
        "metadata_filter": {"field": "value"},
        "search_language": "english_unaccent",
        "extract_keywords": False,
        "trigram_similarity_threshold": None,
    }
    assert post_processing == {
        "include_embeddings": False,
    }


@test("get_search_fn_and_params: vector search request without MMR")
def _():
    request = VectorDocSearchRequest(
        vector=[0.1, 0.2, 0.3],
        limit=5,
        confidence=0.8,
        metadata_filter={"field": "value"},
        mmr_strength=0,
    )

    search_fn, params, post_processing = get_search_fn_and_params(request)

    assert search_fn == search_docs_by_embedding
    assert params == {
        "embedding": [0.1, 0.2, 0.3],
        "k": 5,
        "confidence": 0.8,
        "metadata_filter": {"field": "value"},
    }
    assert post_processing == {
        "include_embeddings": True,
    }


@test("get_search_fn_and_params: vector search request with include_embeddings=False")
def _():
    request = VectorDocSearchRequest(
        vector=[0.1, 0.2, 0.3],
        limit=5,
        confidence=0.8,
        metadata_filter={"field": "value"},
        mmr_strength=0,
        include_embeddings=False,
    )

    search_fn, params, post_processing = get_search_fn_and_params(request)

    assert search_fn == search_docs_by_embedding
    assert params == {
        "embedding": [0.1, 0.2, 0.3],
        "k": 5,
        "confidence": 0.8,
        "metadata_filter": {"field": "value"},
    }
    assert post_processing == {
        "include_embeddings": False,
    }


@test("get_search_fn_and_params: vector search request with MMR")
def _():
    request = VectorDocSearchRequest(
        vector=[0.1, 0.2, 0.3],
        limit=5,
        confidence=0.8,
        metadata_filter={"field": "value"},
        mmr_strength=0.5,
    )

    search_fn, params, post_processing = get_search_fn_and_params(request)

    assert search_fn == search_docs_by_embedding
    assert params == {
        "embedding": [0.1, 0.2, 0.3],
        "k": 10,  # min(limit * 2, limit + 10) with limit=5
        "confidence": 0.8,
        "metadata_filter": {"field": "value"},
    }
    assert post_processing == {
        "include_embeddings": True,
    }


@test("get_search_fn_and_params: hybrid search request")
def _():
    request = HybridDocSearchRequest(
        text="search query",
        vector=[0.1, 0.2, 0.3],
        lang="en",
        limit=5,
        confidence=0.8,
        alpha=0.5,
        metadata_filter={"field": "value"},
        mmr_strength=0,
        trigram_similarity_threshold=0.4,
        k_multiplier=7,
    )

    search_fn, params, post_processing = get_search_fn_and_params(request)

    assert search_fn == search_docs_hybrid
    assert params == {
        "text_query": "search query",
        "embedding": [0.1, 0.2, 0.3],
        "k": 5,
        "confidence": 0.8,
        "alpha": 0.5,
        "metadata_filter": {"field": "value"},
        "search_language": "english_unaccent",
        "extract_keywords": False,
        "trigram_similarity_threshold": None,
        "k_multiplier": 7,
    }
    assert post_processing == {
        "include_embeddings": True,
    }


@test("get_search_fn_and_params: hybrid search request with include_embeddings=False")
def _():
    request = HybridDocSearchRequest(
        text="search query",
        vector=[0.1, 0.2, 0.3],
        lang="en",
        limit=5,
        confidence=0.8,
        alpha=0.5,
        metadata_filter={"field": "value"},
        mmr_strength=0,
        trigram_similarity_threshold=0.4,
        k_multiplier=7,
        include_embeddings=False,
    )

    search_fn, params, post_processing = get_search_fn_and_params(request)

    assert search_fn == search_docs_hybrid
    assert params == {
        "text_query": "search query",
        "embedding": [0.1, 0.2, 0.3],
        "k": 5,
        "confidence": 0.8,
        "alpha": 0.5,
        "metadata_filter": {"field": "value"},
        "search_language": "english_unaccent",
        "extract_keywords": False,
        "trigram_similarity_threshold": None,
        "k_multiplier": 7,
    }
    assert post_processing == {
        "include_embeddings": False,
    }


@test("get_search_fn_and_params: hybrid search request with MMR")
def _():
    request = HybridDocSearchRequest(
        text="search query",
        vector=[0.1, 0.2, 0.3],
        lang="en",
        limit=5,
        confidence=0.8,
        alpha=0.5,
        metadata_filter={"field": "value"},
        mmr_strength=0.5,
        trigram_similarity_threshold=0.4,
        k_multiplier=7,
    )

    search_fn, params, post_processing = get_search_fn_and_params(request)

    assert search_fn == search_docs_hybrid
    assert params == {
        "text_query": "search query",
        "embedding": [0.1, 0.2, 0.3],
        "k": 10,  # min(limit * 2, limit + 10) with limit=5
        "confidence": 0.8,
        "alpha": 0.5,
        "metadata_filter": {"field": "value"},
        "search_language": "english_unaccent",
        "extract_keywords": False,
        "trigram_similarity_threshold": None,
        "k_multiplier": 7,
    }
    assert post_processing == {
        "include_embeddings": True,
    }


@test("get_search_fn_and_params: hybrid search request with invalid language")
def _():
    request = HybridDocSearchRequest(
        text="search query",
        vector=[0.1, 0.2, 0.3],
        lang="en-axzs",  # Invalid language code
        limit=5,
        confidence=0.8,
        alpha=0.5,
        metadata_filter={"field": "value"},
        mmr_strength=0,
        trigram_similarity_threshold=0.4,
        k_multiplier=7,
    )

    with raises(HTTPException) as exc:
        _search_fn, _params, _post_processing = get_search_fn_and_params(request)

    assert exc.raised.status_code == 422
    assert exc.raised.detail == "Invalid ISO 639 language code."


@test("strip_embeddings: single DocReference with embedding")
def _():
    # Create test data
    doc = DocReference(
        id=uuid4(),
        owner=DocOwner(id=uuid4(), role="user"),
        title="Test Document",
        snippet=Snippet(index=0, content="Test content", embedding=[0.1, 0.2, 0.3, 0.4, 0.5]),
        distance=0.8,
    )

    # Test the function
    result = strip_embeddings(doc)

    # Assertions
    assert isinstance(result, DocReference)
    assert result.snippet.embedding is None
    assert result.snippet.content == "Test content"
    assert result.snippet.index == 0
    assert result.title == "Test Document"
    assert result.distance == 0.8


@test("strip_embeddings: single DocReference without embedding")
def _():
    # Create test data without embedding
    doc = DocReference(
        id=uuid4(),
        owner=DocOwner(id=uuid4(), role="agent"),
        title="Test Document",
        snippet=Snippet(index=1, content="Test content without embedding", embedding=None),
    )

    # Test the function
    result = strip_embeddings(doc)

    # Assertions
    assert isinstance(result, DocReference)
    assert result.snippet.embedding is None
    assert result.snippet.content == "Test content without embedding"
    assert result.snippet.index == 1


@test("strip_embeddings: list of DocReferences with embeddings")
def _():
    # Create test data
    docs = [
        DocReference(
            id=uuid4(),
            owner=DocOwner(id=uuid4(), role="user"),
            title="Document 1",
            snippet=Snippet(index=0, content="Content 1", embedding=[0.1, 0.2, 0.3]),
        ),
        DocReference(
            id=uuid4(),
            owner=DocOwner(id=uuid4(), role="agent"),
            title="Document 2",
            snippet=Snippet(index=1, content="Content 2", embedding=[0.4, 0.5, 0.6]),
        ),
    ]

    # Test the function
    result = strip_embeddings(docs)

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 2

    for i, doc in enumerate(result):
        assert isinstance(doc, DocReference)
        assert doc.snippet.embedding is None
        assert doc.snippet.content == f"Content {i + 1}"
        assert doc.title == f"Document {i + 1}"


@test("strip_embeddings: list of DocReferences mixed with and without embeddings")
def _():
    # Create test data with mixed embedding states
    docs = [
        DocReference(
            id=uuid4(),
            owner=DocOwner(id=uuid4(), role="user"),
            title="Document with embedding",
            snippet=Snippet(
                index=0, content="Content with embedding", embedding=[0.1, 0.2, 0.3]
            ),
        ),
        DocReference(
            id=uuid4(),
            owner=DocOwner(id=uuid4(), role="agent"),
            title="Document without embedding",
            snippet=Snippet(index=1, content="Content without embedding", embedding=None),
        ),
    ]

    # Test the function
    result = strip_embeddings(docs)

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 2

    for doc in result:
        assert isinstance(doc, DocReference)
        assert doc.snippet.embedding is None


@test("strip_embeddings: empty list")
def _():
    # Test with empty list
    docs = []

    # Test the function
    result = strip_embeddings(docs)

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 0
