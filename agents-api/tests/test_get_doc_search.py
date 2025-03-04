from agents_api.autogen.openapi_model import (
    HybridDocSearchRequest,
    TextOnlyDocSearchRequest,
    VectorDocSearchRequest,
)
from agents_api.common.utils.get_doc_search import get_language, get_search_fn_and_params
from agents_api.queries.docs.search_docs_by_embedding import search_docs_by_embedding
from agents_api.queries.docs.search_docs_by_text import search_docs_by_text
from agents_api.queries.docs.search_docs_hybrid import search_docs_hybrid
from ward import raises, test


@test("get_language: valid language code returns lowercase language name")
def _():
    result = get_language("en")
    assert result == "english"

    result = get_language("fr")
    assert result == "french"


@test("get_language: invalid language code raises ValueError")
def _():
    with raises(ValueError) as exc:
        # Cast None to str to satisfy type checking while still testing the behavior
        get_language(None)  # type: ignore

    assert str(exc.raised) == "Invalid ISO 639-1 language code."


@test("get_language: empty language code raises ValueError")
def _():
    with raises(ValueError) as exc:
        get_language("")

    assert str(exc.raised) == "Invalid ISO 639-1 language code."


@test("get_language: None language code raises ValueError")
def _():
    with raises(ValueError) as exc:
        # Using a string variable set to None to test the behavior
        none_lang = None  # type: ignore
        get_language(none_lang)  # type: ignore

    assert str(exc.raised) == "Invalid ISO 639-1 language code."


@test("get_search_fn_and_params: text-only search request")
def _():
    request = TextOnlyDocSearchRequest(
        text="search query",
        limit=10,
        lang="en",
        metadata_filter={"field": "value"},
    )

    search_fn, params = get_search_fn_and_params(request)

    assert search_fn == search_docs_by_text
    assert params == {
        "query": "search query",
        "k": 10,
        "metadata_filter": {"field": "value"},
        "search_language": "english",
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

    search_fn, params = get_search_fn_and_params(request)

    assert search_fn == search_docs_by_embedding
    assert params == {
        "embedding": [0.1, 0.2, 0.3],
        "k": 5,
        "confidence": 0.8,
        "metadata_filter": {"field": "value"},
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

    search_fn, params = get_search_fn_and_params(request)

    assert search_fn == search_docs_by_embedding
    assert params == {
        "embedding": [0.1, 0.2, 0.3],
        "k": 15,  # 5 * 3 because MMR is enabled
        "confidence": 0.8,
        "metadata_filter": {"field": "value"},
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
    )

    search_fn, params = get_search_fn_and_params(request)

    assert search_fn == search_docs_hybrid
    assert params == {
        "text_query": "search query",
        "embedding": [0.1, 0.2, 0.3],
        "k": 5,
        "confidence": 0.8,
        "alpha": 0.5,
        "metadata_filter": {"field": "value"},
        "search_language": "english",
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
    )

    search_fn, params = get_search_fn_and_params(request)

    assert search_fn == search_docs_hybrid
    assert params == {
        "text_query": "search query",
        "embedding": [0.1, 0.2, 0.3],
        "k": 15,  # 5 * 3 because MMR is enabled
        "confidence": 0.8,
        "alpha": 0.5,
        "metadata_filter": {"field": "value"},
        "search_language": "english",
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
    )

    with raises(ValueError) as exc:
        _search_fn, _params = get_search_fn_and_params(request)

    assert str(exc.raised) == "Invalid ISO 639-1 language code."
