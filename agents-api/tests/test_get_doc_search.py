import pytest
from agents_api.autogen.openapi_model import HybridDocSearchRequest, TextOnlyDocSearchRequest, VectorDocSearchRequest
from agents_api.common.utils.get_doc_search import get_language, get_search_fn_and_params
from agents_api.queries.docs.search_docs_by_embedding import search_docs_by_embedding
from agents_api.queries.docs.search_docs_by_text import search_docs_by_text
from agents_api.queries.docs.search_docs_hybrid import search_docs_hybrid
from fastapi import HTTPException

def test_get_language_valid_language_code_returns_lowercase_language_name():
    """get_language: valid language code returns lowercase language name"""
    result = get_language('en')
    assert result == 'english_unaccent'
    result = get_language('fr')
    assert result == 'french'

def test_get_language_empty_language_code_raises_httpexception():
    """get_language: empty language code raises HTTPException"""
    with pytest.raises(HTTPException) as exc:
        get_language('')
    assert exc.value.status_code == 422
    assert exc.value.detail == 'Invalid ISO 639 language code.'

def test_get_search_fn_and_params_text_only_search_request():
    """get_search_fn_and_params: text-only search request"""
    request = TextOnlyDocSearchRequest(text='search query', limit=10, lang='en', metadata_filter={'field': 'value'}, trigram_similarity_threshold=0.4)
    search_fn, params = get_search_fn_and_params(request)
    assert search_fn == search_docs_by_text
    assert params == {'query': 'search query', 'k': 10, 'metadata_filter': {'field': 'value'}, 'search_language': 'english_unaccent', 'extract_keywords': False, 'trigram_similarity_threshold': 0.4}

def test_get_search_fn_and_params_vector_search_request_without_mmr():
    """get_search_fn_and_params: vector search request without MMR"""
    request = VectorDocSearchRequest(vector=[0.1, 0.2, 0.3], limit=5, confidence=0.8, metadata_filter={'field': 'value'}, mmr_strength=0)
    search_fn, params = get_search_fn_and_params(request)
    assert search_fn == search_docs_by_embedding
    assert params == {'embedding': [0.1, 0.2, 0.3], 'k': 5, 'confidence': 0.8, 'metadata_filter': {'field': 'value'}}

def test_get_search_fn_and_params_vector_search_request_with_mmr():
    """get_search_fn_and_params: vector search request with MMR"""
    request = VectorDocSearchRequest(vector=[0.1, 0.2, 0.3], limit=5, confidence=0.8, metadata_filter={'field': 'value'}, mmr_strength=0.5)
    search_fn, params = get_search_fn_and_params(request)
    assert search_fn == search_docs_by_embedding
    assert params == {'embedding': [0.1, 0.2, 0.3], 'k': 15, 'confidence': 0.8, 'metadata_filter': {'field': 'value'}}

def test_get_search_fn_and_params_hybrid_search_request():
    """get_search_fn_and_params: hybrid search request"""
    request = HybridDocSearchRequest(text='search query', vector=[0.1, 0.2, 0.3], lang='en', limit=5, confidence=0.8, alpha=0.5, metadata_filter={'field': 'value'}, mmr_strength=0, trigram_similarity_threshold=0.4, k_multiplier=7)
    search_fn, params = get_search_fn_and_params(request)
    assert search_fn == search_docs_hybrid
    assert params == {'text_query': 'search query', 'embedding': [0.1, 0.2, 0.3], 'k': 5, 'confidence': 0.8, 'alpha': 0.5, 'metadata_filter': {'field': 'value'}, 'search_language': 'english_unaccent', 'extract_keywords': False, 'trigram_similarity_threshold': 0.4, 'k_multiplier': 7}

def test_get_search_fn_and_params_hybrid_search_request_with_mmr():
    """get_search_fn_and_params: hybrid search request with MMR"""
    request = HybridDocSearchRequest(text='search query', vector=[0.1, 0.2, 0.3], lang='en', limit=5, confidence=0.8, alpha=0.5, metadata_filter={'field': 'value'}, mmr_strength=0.5, trigram_similarity_threshold=0.4, k_multiplier=7)
    search_fn, params = get_search_fn_and_params(request)
    assert search_fn == search_docs_hybrid
    assert params == {'text_query': 'search query', 'embedding': [0.1, 0.2, 0.3], 'k': 15, 'confidence': 0.8, 'alpha': 0.5, 'metadata_filter': {'field': 'value'}, 'search_language': 'english_unaccent', 'extract_keywords': False, 'trigram_similarity_threshold': 0.4, 'k_multiplier': 7}

def test_get_search_fn_and_params_hybrid_search_request_with_invalid_language():
    """get_search_fn_and_params: hybrid search request with invalid language"""
    request = HybridDocSearchRequest(text='search query', vector=[0.1, 0.2, 0.3], lang='en-axzs', limit=5, confidence=0.8, alpha=0.5, metadata_filter={'field': 'value'}, mmr_strength=0, trigram_similarity_threshold=0.4, k_multiplier=7)
    with pytest.raises(HTTPException) as exc:
        _search_fn, _params = get_search_fn_and_params(request)
    assert exc.value.status_code == 422
    assert exc.value.detail == 'Invalid ISO 639 language code.'