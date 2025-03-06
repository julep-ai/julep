from typing import Any

from fastapi import HTTPException
from langcodes import Language

from ...autogen.openapi_model import (
    HybridDocSearchRequest,
    TextOnlyDocSearchRequest,
    VectorDocSearchRequest,
)
from ...queries.docs.search_docs_by_embedding import search_docs_by_embedding
from ...queries.docs.search_docs_by_text import search_docs_by_text
from ...queries.docs.search_docs_hybrid import search_docs_hybrid


def get_language(lang: str) -> str:
    error_msg = "Invalid ISO 639 language code."

    if not lang or not isinstance(lang, str):
        raise HTTPException(status_code=422, detail=error_msg)

    try:
        language_obj = Language.get(lang)

        # Validate language code
        if not language_obj.is_valid():
            raise HTTPException(status_code=422, detail=error_msg)

        # Check for malformed complex language tags
        if "-" in lang and not (language_obj.territory or language_obj.script):
            parts = lang.split("-")
            if len(parts) > 1 and any(len(part) > 3 for part in parts[1:]):
                raise HTTPException(status_code=422, detail=error_msg)

        # Get language name from description
        language = language_obj.describe().get("language", "english")
        if not language:
            raise HTTPException(status_code=422, detail="Language description is empty")

        # Special case for English
        return "english_unaccent" if language.lower() == "english" else language.lower()

    except (ValueError, AttributeError, KeyError):
        raise HTTPException(status_code=422, detail=error_msg)


def get_search_fn_and_params(
    search_params,
    *,
    extract_keywords: bool = False,
) -> tuple[Any, dict[str, float | int | str | dict[str, float] | list[float]] | None]:
    search_fn, params = None, None

    match search_params:
        case TextOnlyDocSearchRequest(
            text=query,
            limit=k,
            lang=lang,
            metadata_filter=metadata_filter,
        ):
            search_language = get_language(lang)
            search_fn = search_docs_by_text
            params = {
                "query": query,
                "k": k,
                "metadata_filter": metadata_filter,
                "search_language": search_language,
                "extract_keywords": extract_keywords,
            }

        case VectorDocSearchRequest(
            vector=embedding,
            limit=k,
            confidence=confidence,
            metadata_filter=metadata_filter,
        ):
            search_fn = search_docs_by_embedding
            params = {
                "embedding": embedding,
                "k": k * 3 if search_params.mmr_strength > 0 else k,
                "confidence": confidence,
                "metadata_filter": metadata_filter,
            }

        case HybridDocSearchRequest(
            text=query,
            vector=embedding,
            lang=lang,
            limit=k,
            confidence=confidence,
            alpha=alpha,
            metadata_filter=metadata_filter,
        ):
            search_language = get_language(lang)
            search_fn = search_docs_hybrid
            params = {
                "text_query": query,
                "embedding": embedding,
                "k": k * 3 if search_params.mmr_strength > 0 else k,
                "confidence": confidence,
                "alpha": alpha,
                "metadata_filter": metadata_filter,
                "search_language": search_language,
                "extract_keywords": extract_keywords,
            }

    # Note: connection_pool will be passed separately by the caller
    return search_fn, params
